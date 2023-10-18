import requests
from jose import jwt
from jose.exceptions import JOSEError
import os

# NOTE mostly generated from gpt

USER_POOL_ID = os.environ["COGNITO_USER_POOL_ID"]
REGION = os.environ["REGION"]

JWKS_URL = f"https://cognito-idp.{REGION}.amazonaws.com/{USER_POOL_ID}/.well-known/jwks.json"
jwks = requests.get(JWKS_URL).json()


def lambda_handler(event, context):
    token = event["headers"]["Auth"].replace("Bearer ", "")

    try:
        # Decode the token. This will also verify it.
        decoded_token = jwt.decode(token, jwks, algorithms=["RS256"])

        # Here, the token is valid. You can extract claims if you need them.
        user_id = decoded_token["sub"]
        # Add other processing as needed...

        # Return an IAM policy that allows the request. Adjust the policy as needed.
        return generate_allow_policy(user_id, event["methodArn"])

    except JOSEError as e:
        # Token is invalid. Return a deny policy.
        return generate_deny_policy("user", event["methodArn"])


def generate_allow_policy(principal_id, resource):
    return {
        "principalId": principal_id,
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [{"Action": "execute-api:Invoke", "Effect": "Allow", "Resource": resource}],
        },
    }


def generate_deny_policy(principal_id, resource):
    return {
        "principalId": principal_id,
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [{"Action": "execute-api:Invoke", "Effect": "Deny", "Resource": resource}],
        },
    }
