"""DynamoDB access layer.

Points at DynamoDB Local (http://localhost:8000) by default; override with
the DYNAMODB_ENDPOINT env var (set it empty to use real AWS endpoints).

Tables:
  users          - username (S, HASH) -> password_hash
  user_interests - username (S, HASH) -> interests (list of strings)
  nonprofits     - category (S, HASH) + rank (N, RANGE) -> name, city, revenue, ...
"""

import os

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from werkzeug.security import check_password_hash, generate_password_hash
from decimal import Decimal

USERS_TABLE = "users"
INTERESTS_TABLE = "user_interests"
NONPROFITS_TABLE = "nonprofits"


def get_resource():
    endpoint = os.environ.get("DYNAMODB_ENDPOINT", "http://localhost:8000")
    return boto3.resource(
        "dynamodb",
        endpoint_url=endpoint or None,
        region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID", "local"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY", "local"),
    )


def create_tables(resource=None):
    """Create the tables if they don't already exist."""
    resource = resource or get_resource()
    existing = {t.name for t in resource.tables.all()}
    for name in (USERS_TABLE, INTERESTS_TABLE):
        if name in existing:
            continue
        table = resource.create_table(
            TableName=name,
            KeySchema=[{"AttributeName": "username", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "username", "AttributeType": "S"}
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        table.wait_until_exists()
    if NONPROFITS_TABLE not in existing:
        table = resource.create_table(
            TableName=NONPROFITS_TABLE,
            KeySchema=[
                {"AttributeName": "category", "KeyType": "HASH"},
                {"AttributeName": "rank", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "category", "AttributeType": "S"},
                {"AttributeName": "rank", "AttributeType": "N"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        table.wait_until_exists()
    return resource


# ---- users ----

def create_user(resource, username, password, name=None):
    """Store a new user. Returns False if the username is taken."""
    item = {
        "username": username,
        "password_hash": generate_password_hash(password),
    }
    if name:
        item["name"] = name
    try:
        resource.Table(USERS_TABLE).put_item(
            Item=item,
            ConditionExpression="attribute_not_exists(username)",
        )
    except ClientError as err:
        if err.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return False
        raise
    return True


def get_user(resource, username):
    item = resource.Table(USERS_TABLE).get_item(
        Key={"username": username}
    ).get("Item")
    return item


def verify_user(resource, username, password):
    user = get_user(resource, username)
    return bool(user) and check_password_hash(user["password_hash"], password)


def set_password(resource, username, password):
    """Update the password for an existing user. Returns False if unknown."""
    try:
        resource.Table(USERS_TABLE).update_item(
            Key={"username": username},
            UpdateExpression="SET password_hash = :h",
            ConditionExpression="attribute_exists(username)",
            ExpressionAttributeValues={":h": generate_password_hash(password)},
        )
    except ClientError as err:
        if err.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return False
        raise
    return True


# ---- interests ----

def set_interests(resource, username, interests):
    resource.Table(INTERESTS_TABLE).put_item(
        Item={"username": username, "interests": list(interests)}
    )


def get_interests(resource, username):
    item = resource.Table(INTERESTS_TABLE).get_item(
        Key={"username": username}
    ).get("Item")
    return item["interests"] if item else []


# ---- nonprofits ----

def seed_nonprofits(resource, nonprofits):
    """Load nonprofit records (dicts with a category and rank) into the table."""
    with resource.Table(NONPROFITS_TABLE).batch_writer() as batch:
        for org in nonprofits:
            batch.put_item(Item=org)


def get_nonprofits_by_category(resource, category, limit=5):
    """Top nonprofits for one category, ordered by overall revenue rank."""
    items = resource.Table(NONPROFITS_TABLE).query(
        KeyConditionExpression=Key("category").eq(category),
        Limit=limit,
    ).get("Items", [])
    return items


def add_interests(resource, username, interests):
    """Append interests (deduplicated, order preserved) and return the list."""
    merged = get_interests(resource, username)
    for interest in interests:
        if interest not in merged:
            merged.append(interest)
    set_interests(resource, username, merged)
    return merged


def get_co2_saved(resource, username):
    user = get_user(resource, username)
    if not user:
        return 0.0
    return float(user.get("co2_saved", 0))


def add_co2_saved(resource, username, amount):
    resource.Table(USERS_TABLE).update_item(
        Key={"username": username},
        UpdateExpression="""
            SET co2_saved = if_not_exists(co2_saved, :zero) + :amount
        """,
        ExpressionAttributeValues={
            ":amount": Decimal(str(amount)),
            ":zero": Decimal(0)
        }
    )