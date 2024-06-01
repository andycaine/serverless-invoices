# serverless-invoices

A serverless invoices application.

## Description

`serverless-invoices` provides an SQS queue to request invoice generation, and a web endpoint to retrieve generated invoices. `serverless-invoices` uses [invoicely](https://github.com/andycaine/invoicely) to generate invoices. Authentication and authorisation can be added to the web endpoint using [authy](https://github.com/andycaine/authy).

## Getting started

`serverless-invoices` is available via the AWS Serverless Application Repository. You need to provide some invoice generation configuration options via a Lambda layer. The configuration file should look something like this:

```yaml
provider:
  address_line_1: Address Line 1
  address_line_2: Address Line 2
  address_line_3: Address Line 3
  address_line_4: Address Line 4
  address_line_5: Address Line 5
  email: test@andycaine.com
  phone: 01234567890
  vat_number: 123 456 999
logo:
  filename: 'invoicely_100_100.png'
  width: 100
  height: 100
line_item_col_widths:  # represents fractions of the page width
  - 0.5
  - 0.1
  - 0.2
  - 0.2
```

and stored in the root of the Lambda layer directory as `config.yaml`. For example:

```
invoicely-config/
  config.yaml
  invoicely_100_100.png
```

Then we can build a Lambda layer containing this config and deploy `serverless-invoices` in a CloudFormation template:

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: 'AWS::Serverless-2016-10-31'
Description: Invoices stack.
Resources:

  ConfigLayerArn:
    Type: AWS::Serverless::LayerVersion
    Properties:
      LayerName: PDPLayer
      Description: PDPLayer
      ContentUri: pdp/
      CompatibleRuntimes:
        - python3.12
      CompatibleArchitectures:
        - arm64
      RetentionPolicy: Delete
    Metadata:
      BuildMethod: python3.12
      BuildArchitecture: arm64

  Invoices:
    Type: AWS::Serverless::Application
    Properties:
      Location:
        ApplicationId: 'arn:aws:serverlessrepo:eu-west-2:211125310871:applications/serverless-invoices'
        SemanticVersion: <CURRENT_VERSION>
      Parameters:
        ConfigLayerArn: !Ref ConfigLayerArn
```

Then you can deploy your stack. These steps assume you have the [SAM CLI installed and set up for your environment](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html):

```
$ sam build
$ sam deploy \
    --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND \
    --stack-name example-stack \
    --resolve-s3
```

## Adding Authentication and Authorisation

[authy](https://github.com/andycaine/authy) can be used to add authentication and authorisation services:

```yaml
Authy:
  Type: AWS::Serverless::Application
  Properties:
    Location:
      ApplicationId: 'arn:aws:serverlessrepo:eu-west-2:211125310871:applications/authy'
      SemanticVersion: <CURRENT_VERSION>
    Parameters:
      ...

Invoices:
  Type: AWS::Serverless::Application
  Properties:
    Location:
      ApplicationId: 'arn:aws:serverlessrepo:eu-west-2:211125310871:applications/serverless-invoices'
      SemanticVersion: <CURRENT_VERSION>
    Parameters:
      LambdaAuthorizerArn: !GetAtt Authy.Outputs.CognitoAbacAuthorizerArn
      LambdaAuthorizerRoleArn: !GetAtt Authy.Outputs.LambdaAuthorizerRoleArn
      ...

```
