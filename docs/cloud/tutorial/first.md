# First Cloud Flow

## Write Flow

Below is an example Flow you may use for this tutorial.

```python
import prefect
from prefect import task, Flow

@task
def hello_task():
    logger = prefect.context.get("logger")
    logger.info("Hello, Cloud!")

flow = Flow("hello-flow", tasks=[hello_task])
```

Note that this Flow can be run locally by calling `flow.run()`, however, it currently does not yet use any Prefect Cloud features.

## Register Flow with Prefect Cloud

In order to take advantage of Prefect Cloud for your Flow, that Flow must first be _registered_. Registration of a Flow sends a Flow's metadata to Prefect Cloud in order to support its orchestration.

Add the following line to the bottom of the example Flow to register the Flow with Prefect Cloud:

```python
flow.register(project_name="Hello, World!")
```

A Flow must be registered to a specific Project; in this case we are using the default `Hello, World!` Project.

::: tip Flow Code
Registration only sends data about the existence and format of your Flow; **no actual code from the Flow is sent to Prefect Cloud**. Your code remains safe, secure, and private in your own infrastructure!
:::

## Run Flow with Prefect Cloud

Now that your script is registered with Prefect Cloud, we will use an Agent to watch for Flow Runs that are scheduled by Prefect Cloud and execute them accordingly.

The simplest way to start an [Local Agent](/cloud/agents/local.html) is right from within your script. Add the following line to the bottom of your Flow:

```python
flow.run_agent()
```

::: tip Runner Token
This Local Agent will use the _RUNNER_ token stored in your environment but if you want to manually pass it a token you may do so with `run_agent(token=<YOUR_RUNNER_TOKEN>)`.
:::

Lastly, we need to indicate to Cloud to schedule a Flow Run; there are a few options at your disposal to do this:

:::: tabs
::: tab CLI

```bash
prefect run cloud --name hello-flow --project 'Hello, World!'
```

:::
::: tab UI
Navigate to the UI and click _Run_ on your Flow's page
:::
::: tab "GraphQL API"

```graphql
mutation {
  createFlowRun(input: { flowId: "<flow id>" }) {
    id
  }
}

```

See [Flow Runs](/cloud/concepts/flow_runs.html#flow-runs) for more details.
:::
::: tab Python

```python
from prefect import Client

c = Client()
c.create_flow_run(flow_id="<flow id>")
```

:::
::::

Notice the result of your Flow Run in the Agent output in your terminal.

Remember to stop the agent with `Ctrl-C`.
