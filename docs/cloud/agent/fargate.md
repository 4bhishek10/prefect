# Fargate Agent

The Fargate Agent is an agent designed to deploy flows as Tasks using AWS Fargate. This agent can be run anywhere so long as the proper AWS configuration credentials are provided.

[[toc]]

### Requirements

When running the Fargate you may optionally provide `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_SESSION_TOKEN` (specific to temporary credentials). If these three items are not explicitly defined, boto3 will default to environment variables or your credentials file. Having the `REGION_NAME` defined along with the appropriate credentials stored per aws expectations are required to initialize the [boto3 client](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ecs.html#client). For more information on properly setting your credentials, check out the boto3 documentation [here](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html).

### Usage

```
$ prefect agent start fargate

 ____            __           _        _                    _
|  _ \ _ __ ___ / _| ___  ___| |_     / \   __ _  ___ _ __ | |_
| |_) | '__/ _ \ |_ / _ \/ __| __|   / _ \ / _` |/ _ \ '_ \| __|
|  __/| | |  __/  _|  __/ (__| |_   / ___ \ (_| |  __/ | | | |_
|_|   |_|  \___|_|  \___|\___|\__| /_/   \_\__, |\___|_| |_|\__|
                                           |___/

2019-08-27 14:33:39,772 - agent - INFO - Starting FargateAgent
2019-08-27 14:33:39,772 - agent - INFO - Agent documentation can be found at https://docs.prefect.io/cloud/
2019-08-27 14:33:40,932 - agent - INFO - Agent successfully connected to Prefect Cloud
2019-08-27 14:33:40,932 - agent - INFO - Waiting for flow runs...
```

The Fargate Agent can be started either through the Prefect CLI or by importing the `FargateAgent` class from the core library. Starting the agent from the CLI will require that the required AWS configuration arguments are set at the environment level while importing the agent class in a Python process will allow you to specify them at initialization.

::: tip Tokens
There are a few ways in which you can specify a `RUNNER` API token:

- command argument `prefect agent start fargate -t MY_TOKEN`
- environment variable `export PREFECT__CLOUD__AGENT__AUTH_TOKEN=MY_TOKEN`
- token will be used from `prefect.config.cloud.auth_token` if not provided from one of the two previous methods

:::

### Installation

Unlike the Kubernetes Agent, the Fargate Agent is not generally installed to run on Fargate itself and instead it can be spun up anywhere with the correct variables set.

Through the Prefect CLI:

```
$ export AWS_ACCESS_KEY_ID=MY_ACCESS
$ export AWS_SECRET_ACCESS_KEY=MY_SECRET
$ export AWS_SESSION_TOKEN=MY_SESSION
$ export REGION_NAME=MY_REGION
$ prefect agent start fargate
```

In a Python process:

```python
from prefect.agent.fargate import FargateAgent

agent = FargateAgent(
        aws_access_key_id="MY_ACCESS",
        aws_secret_access_key="MY_SECRET",
        aws_session_token="MY_SESSION",
        region_name="MY_REGION",
        )

agent.start()
```

You are now ready to run some flows!

### Process

The Fargate Agent periodically polls for new flow runs to execute. When a flow run is retrieved from Prefect Cloud the agent checks to make sure that the flow was registered with a Docker storage option. If so, the agent then creates a Task using the `storage` attribute of that flow, and runs `prefect execute cloud-flow`.

If it is the first run of a particular flow then a Task Definition will be registered. Each new run of that flow will run using that same Task Definition and it will override some of the environment variables in order to specify which flow run is occurring.

When the flow run is found and the Task is run the logs of the agent should reflect that:

```
2019-09-01 19:00:30,532 - agent - INFO - Starting FargateAgent
2019-09-01 19:00:30,533 - agent - INFO - Agent documentation can be found at https://docs.prefect.io/cloud/
2019-09-01 19:00:30,655 - agent - INFO - Agent successfully connected to Prefect Cloud
2019-09-01 19:00:30,733 - agent - INFO - Waiting for flow runs...
2019-09-01 19:01:08,835 - agent - INFO - Found 1 flow run(s) to submit for execution.
2019-09-01 19:01:09,158 - agent - INFO - Submitted 1 flow run(s) for execution.
```

The Fargate Task run should be created and it will start in a `PENDING` state. Once the resources are provisioned it will enter a `RUNNING` state and on completion it will finish as `COMPLETED`.

### Configuration

The Fargate Agent allows for a set of AWS configuration options to be set or provided in order to initialize the boto3 client. All of these options can be provided at initialization of the `FargateAgent` class or through an environment variable:

- aws_access_key_id (str, optional): AWS access key id for connecting the boto3 client. Defaults to the value set in the environment variable `AWS_ACCESS_KEY_ID`.
- aws_secret_access_key (str, optional): AWS secret access key for connecting the boto3 client. Defaults to the value set in the environment variable `AWS_SECRET_ACCESS_KEY`.
- aws_session_token (str, optional): AWS session key for connecting the boto3 client. Defaults to the value set in the environment variable `AWS_SESSION_TOKEN`.
- region_name (str, optional): AWS region name for connecting the boto3 client. Defaults to the value set in the environment variable `REGION_NAME`.

While the above configuration options allow for the initialization of the boto3 client, you may also need to specify the arguments that allow for the registering and running of Fargate task definitions. The Fargate Agent makes no assumptions on how your particular AWS configuration is set up and instead has a `kwargs` argument which will accept any arguments for boto3's `register_task_definition` and `run_task` functions.

Accepted kwargs for [`register_task_definition`](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ecs.html#ECS.Client.register_task_definition):

```
taskRoleArn                 string
executionRoleArn            string
volumes                     list
placementConstraints        list
cpu                         string
memory                      string
tags                        list
pidMode                     string
ipcMode                     string
proxyConfiguration          dict
inferenceAccelerators       list
```

Accepted kwargs for [`run_task`](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ecs.html#ECS.Client.run_task):

```
cluster                     string
count                       integer
startedBy                   string
group                       string
placementConstraints        list
placementStrategy           list
platformVersion             string
networkConfiguration        dict
tags                        list
enableECSManagedTags        boolean
propagateTags               string
```

:::tip boto3 kwargs
For more information on using Fargate with boto3 and to see the list of supported configuration options please visit the [relevant API documentation.](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ecs.html) Most importantly the functions [register_task_definition()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ecs.html#ECS.Client.register_task_definition)and [run_task()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ecs.html#ECS.Client.run_task).
:::

All of these options can be provided at initialization of the `FargateAgent` class or through an environment variable. This means that the environment variables will need to be string representations of the values they represent.

For example, the `networkConfiguration` kwarg accepts a dictionary and if provided through an environment variable it will need to be a string representation of that dictionary.

```python
networkConfiguration={
    "awsvpcConfiguration": {
        "assignPublicIp": "ENABLED",
        "subnets": ["my_subnet_id"],
        "securityGroups": []
    }
}
```

```bash
networkConfiguration="{'awsvpcConfiguration': {'assignPublicIp': 'ENABLED', 'subnets': ['my_subnet_id'], 'securityGroups': []}}"
```


:::warning Case Sensitive Environment Variables
Please note that when setting the boto3 configuration for the `register_task_definition` and `run_task` the keys are case sensitive. For example: if setting placement constraints through an environment variable it must match boto3's case sensitive `placementConstraints`.
:::

### Configuration Examples

Below are two minimal examples which specify information for connecting to boto3 as well as the task's resource requests and network configuration. The first example initializes a `FargateAgent` with kwargs passed in and the second example uses the Prefect CLI to start the Fargate Agent with kwargs being loaded from environment variables.

#### Python Script

```python
from prefect.agent.fargate import FargateAgent

agent = FargateAgent(
    aws_access_key_id="...",
    aws_secret_access_key="...",
    region_name="us-east-1",
    cpu="256",
    memory="512",
    networkConfiguration={
        "awsvpcConfiguration": {
            "assignPublicIp": "ENABLED",
            "subnets": ["my_subnet_id"],
            "securityGroups": []
        }
    }
)

agent.start()
```

#### Prefect CLI

```bash
$ export AWS_ACCESS_KEY_ID=...
$ export AWS_SECRET_ACCESS_KEY=...
$ export REGION_NAME=us-east-1
$ export cpu=256
$ export memory=512
$ export networkConfiguration="{'awsvpcConfiguration': {'assignPublicIp': 'ENABLED', 'subnets': ['my_subnet_id'], 'securityGroups': []}}"

$ prefect agent start fargate
```


:::warning Outbound Traffic
If you encounter issues with Fargate raising errors in cases of client timeouts or inability to pull containers then you may need to adjust your `networkConfiguration`. Visit [this discussion thread](https://github.com/aws/amazon-ecs-agent/issues/1128#issuecomment-351545461) for more information on configuring AWS security groups.
:::

#### Prefect CLI Using Kwargs

All configuration options for the Fargate Agent can also be provided to the `prefect agent start fargate` CLI command. They must match the camel casing used by boto3 but both the single kwarg as well as with the standard prefix of `--` are accepted. This means that `taskRoleArn=""` is the same as `--taskRoleArn=""`.

```bash
$ export AWS_ACCESS_KEY_ID=...
$ export AWS_SECRET_ACCESS_KEY=...
$ export REGION_NAME=us-east-1

$ prefect agent start fargate cpu=256 memory=512 networkConfiguration="{'awsvpcConfiguration': {'assignPublicIp': 'ENABLED', 'subnets': ['my_subnet_id'], 'securityGroups': []}}"
```

Kwarg values can also be provided through environment variables. This is useful in situations where case sensitive environment variables are desired or when using templating tools like Terraform to deploy your Agent.

```bash
$ export AWS_ACCESS_KEY_ID=...
$ export AWS_SECRET_ACCESS_KEY=...
$ export REGION_NAME=us-east-1
$ export CPU=256
$ export MEMORY=512
$ export NETWORK_CONFIGURATION="{'awsvpcConfiguration': {'assignPublicIp': 'ENABLED', 'subnets': ['my_subnet_id'], 'securityGroups': []}}"

$ prefect agent start fargate cpu=$CPU memory=$MEMORY networkConfiguration=$NETWORK_CONFIGURATION
```
