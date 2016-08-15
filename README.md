# oauth-passthrough
Allows username and password information to be passed through oauth tokens.

## Why would you want this?
I want to write an [Alexa skill](https://developer.amazon.com/public/solutions/alexa/alexa-skills-kit/docs/developing-an-alexa-skill-as-a-lambda-function) for [Baby Tracker](http://nighp.com/babytracker). This requires me to be able to link the Alexa user to the Baby Tracker user. But the former only allows linking via OAuth while the latter only allows authorization via username and password. This project provides an OAuth endpoint that will take a username (email) and password from a user and return that as the OAuth token, which will allow me to effectively link the two accounts.

Even better, these OAuth tokens will be stored by Amazon, and the integration will only have access to them when the Alexa skill is invoked. And the tokens can be encrypted to protect against the unfortunate situation where Amazon's token store is breached.

## Deployment
### Lambda function
From the oauth-passthrough directory:

* Install [PyCrypto](https://github.com/dlitz/pycrypto) to your local checkout of this code. PyCrypto contains compiled modules, so you'll need to get a version that's been compiled in an AWS version of Linux. Since PyCrypto is already installed on in AWS Linux, the easiest way to do this is just to spin up a small EC2 instance and run
```
rsync -r ec2-user@YOUR_EC2_INSTANCE_IP:/usr/lib64/python2.7/dist-packages/Crypto .
```
* Create a new public / private keypair to use with oauth-passthrough
```
ssh-keygen -N "" -f oauth_passthrough.key
```
* Edit `oauth_passthrough.py` to update `REDIRECT_URI` and `CLIENT_ID` to match the OAuth client you want to serve.
* Zip `oauth_passthrough.py` and all its requirements
```
zip -r oauth_passthrough oauth_passthrough.py oauth_passthrough.key.pub Crypto
```
or to slim down the zipfile
```
zip oauth_passthrough oauth_passthrough.py oauth_passthrough.key.pub `find Crypto | grep -v pyc$ | grep -v SelfTest`
```
* Create an [AWS Lambda](https://aws.amazon.com/lambda/) function with the resulting `oauth_passthrough.zip`. If you name this something other than "OAuthPassthrough", you should update `create_api_gateway.py` with the new function name.

### API Gateway
Fill your AWS account id into `create_api_gateway.py` and run it. This will create an [API Gateway](https://aws.amazon.com/api-gateway/) to match your lambda function, resulting in your lambda function basically being a webserver. Note that you'll still need to deploy the API Gateway after testing that it works as expected. Once deployed, this will provide you with an endpoint that you can provide to your OAuth client.
