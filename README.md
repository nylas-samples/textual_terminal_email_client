# Create a Terminal Email Client using Textual and Python 

This project will show you how to create a Terminal Email Client to read, reply, delete and compose emails.

## Setup

### System dependencies

- Python v3.x

### Gather environment variables

You'll need the following values:

```text
NYLAS_API_KEY =
NYLAS_API_URI =
GRANT_ID =
```

Add the above values to a new `.env` file:

```bash
$ touch .env # Then add your env variables
```

### Install dependencies

```bash
$ pip3 install textual[dev]
# pip3 install beautifulsoup4
```

## Usage

Clone the repository. Go to your terminal and type:

```bash
$ cd terminal_email_client
$ python3 email_client.py
```
# Or you can simply run:

```bash
pip install textual-email-client
```

Once installed, you will need to create an .env where the package was installed, for this you can use:

```bash
pip show text-email-client
```

Copy the location and then do:

```
nano /opt/homebrew/lib/python3.12/site-packages/.env
```

Using the the following values (Fill them with your Nylas information):

```text
NYLAS_API_KEY =
NYLAS_API_URI =
GRANT_ID =
```

Once installed you can call it straight from your terminal as:

```
emailClient
```

Visit our [Nylas Python SDK documentation](https://developer.nylas.com/docs/developer-tools/sdk/python-sdk/) to learn more.
