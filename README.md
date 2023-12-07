# Create a Terminal Email Client using Textual and Python 

This project will show you how to create a Terminal Email Client to read, reply, delete and compose emails.

## Setup

### System dependencies

- Python v3.x

### Gather environment variables

You'll need the following values:

```text
V3_TOKEN =
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

## Learn more

Visit our [Nylas Python SDK documentation](https://developer.nylas.com/docs/developer-tools/sdk/python-sdk/) to learn more.
