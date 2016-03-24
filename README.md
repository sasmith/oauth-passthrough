# oauth-passthrough
Allows username and password information to be passed through oauth tokens.

## Why would you want this?
I want to write an [Alexa skill](https://developer.amazon.com/public/solutions/alexa/alexa-skills-kit/docs/developing-an-alexa-skill-as-a-lambda-function) for [Baby Tracker](http://nighp.com/babytracker). This requires me to be able to link the Alexa user to the Baby Tracker user. But the former only allows linking via OAuth while the latter only allows authorization via username and email. This project provides an OAuth endpoint that will take a username (email) and password from a user and return that as the OAuth token, which will allow me to effectively link the two accounts.

Even better, these OAuth tokens will be stored by Amazon, and the integration will only have access to them when the Alexa skill is invoked. And the tokens can be encrypted to protect against the unfortunate situation where Amazon's token store is breached.

## Deployment
### The Lambda function
Create an [AWS Lambda](https://aws.amazon.com/lambda/) function with code `lambda.py`. The `REDIRECT_URI` and `CLIENT_ID` should be filled in manually to match the OAuth client you want to serve. Then fill your AWS account id into `create_api_gateway.py` and run it. This will create an [API Gateway](https://aws.amazon.com/api-gateway/) to match your lambda function, resulting in your lambda function basically being a webserver. Note that you'll still need to deploy the API Gateway after testing that it works as expected.
