# Import your dependencies
from dotenv import load_dotenv
import os
from rich.text import Text
from nylas import APIClient  # type: ignore
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import DataTable, Label, Header, Footer, Input, Button
from textual.screen import Screen
from textual.binding import Binding
import datetime
from bs4 import BeautifulSoup
import textwrap
from typing import List, Any

# Load your env variables
load_dotenv()

# Initialize an instance of the Nylas SDK using the client credentials
nylas = APIClient(
    os.environ.get("CLIENT_ID"),
    os.environ.get("CLIENT_SECRET"),
    os.environ.get("ACCESS_TOKEN"),
)

# Create the header of the Data Table
ROWS = [("Date", "Subject", "From", "Unread")]

# Global variables
messageid = []
labelsDict = {}
labels = nylas.labels.all()
for label in labels:
    labelsDict[label["name"]] = label["id"]

# Get the body of a particular message clean of HTML tags
def get_message(self, message_id: str) -> str:
    body = ""
    message = nylas.messages.get(message_id)
    soup = BeautifulSoup(message.body, "html.parser")
    for data in soup(["style", "script"]):
        data.decompose()
    wrapper = textwrap.TextWrapper(width=75)
    word_list = wrapper.wrap(text=" ".join(soup.stripped_strings))
    body = ""
    for word in word_list:
        body = body + word + "\n"
    if self is not None:
        try:
            message.mark_as_read()
            message.save()
        except Exception:
            if message.unread == True: 
                self.populate_table()
    return body

# Read the first 5 messages of our inbox
def get_messages() -> List[Any]:
    messages = nylas.messages.where(in_="inbox", limit=5)
    ROWS.clear()
    ROWS.append(("Date", "Subject", "From", "Unread"))
    for message in messages:
        _from = message.from_[0]["name"] + " / " + message.from_[0]["email"]
        ROWS.append(
            (
                datetime.datetime.fromtimestamp(message.date).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                message.subject[0:50],
                _from,
                message.unread,
            )
        )
    return messages

# This can be considered the main screen
class EmailApp(App):
# Setup the bindings for the footer	
    BINDINGS = [
        Binding("r", "refresh", "Refresh"),
        Binding("s", "send", "Send", show=False),
        Binding("c", "cancel", "Cancel", show=False),
        Binding("d", "delete", "Delete"),
        Binding("o", "compose", "Compose Email"),
        Binding("p", "reply", "Reply"),
    ]

# Class variables
    messages = [Any]
    id_message = 0

# Fill up the Data table
    def populate_table(self) -> None:
        self.messages = get_messages()
        table = self.query_one(DataTable)
        table.clear()
        table.cursor_type = "row"
        rows = iter(ROWS)
        counter = 0
        for row in rows:
            if counter > 0:
                if row[3] is True:
                    styled_row = [
                        Text(str(cell), style="bold #03AC13") for cell in row
                    ]
                    table.add_row(*styled_row)
                else:    
                    table.add_row(*row)
            counter += 1

# Load up the main components of the screen
    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield DataTable()
        yield Label(id="message")

# After we load the components, fill up their data
    def on_mount(self) -> None:		
        self.messages = get_messages()
        table = self.query_one(DataTable)
        table.cursor_type = "row"
        rows = iter(ROWS)
        table.add_columns(*next(rows))
        for row in rows:
            if row[3] is True:
                styled_row = [
                    Text(str(cell), style="bold #03AC13") for cell in row
                ]
                table.add_row(*styled_row)
            else:    
                table.add_row(*row)

# When we select a line on our Data table, or read
# an email
    def on_data_table_row_selected(self, event) -> None:
        message = self.query_one("#message", Label)
        self.id_message = self.messages[event.cursor_row].id
        messageid.clear()
        messageid.append(self.id_message)
        message.update(get_message(self, self.id_message))

# We're deleting an email
    def action_delete(self) -> None:
        try:
            _message = nylas.messages.get(self.id_message)
            _message.add_label(labelsDict["trash"])
            _message.save()
        except Exception as e:
            pass
            self.populate_table()

# We want to Compose a new email
    def action_compose(self) -> None:
        self.push_screen(ComposeEmail())

# We want to refresh by calling in new emails
    def action_refresh(self) -> None:
        self.populate_table()

# We want to reply to an email
    def action_reply(self) -> None:
        if len(messageid) > 0:
            self.push_screen(ReplyScreen())

# Reply screen. This screen we will be displayed when we are
# replying an email
class ReplyScreen(Screen):
# Setup the bindings for the footer	
    BINDINGS = [
        Binding("r", "refresh", "Refresh", show=False),
        Binding("s", "send", "Send"),
        Binding("c", "cancel", "Cancel"),
        Binding("d", "delete", "Delete", show=False),
        Binding("o", "compose", "Compose Email", show=False),
        Binding("p", "reply", "Reply", show=False),
    ]

# Load up the main components of the screen
    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield Input(id="email_from")
        yield Input(id="title")
        yield Label(id="body")
        yield Label("======================")
        yield Input(id="first")
        yield Input(id="second")
        yield Input(id="third")
        yield Input(id="fourth")
        yield Horizontal(
            Button("Send!", variant="primary", id="send"),
            Label(" "),
            Button("Cancel", variant="primary", id="cancel"),
        )

# After we load the components, fill up their data
    def on_mount(self) -> None:
        message = nylas.messages.get(messageid[0])
        body = self.query_one("#body", Label)
        self.query_one("#email_from").value = message.from_[0]["email"]
        self.query_one("#title").value = "Re: " + message.subject
        body.update(get_message(None, messageid[0]))

# Grab the information and send the reply to the email
    def send_email(self) -> None:
        participants = []
        draft = nylas.drafts.create()
        list_of_emails = self.query_one("#email_from").value.split(";")
        draft.subject = self.query_one("#title").value
        draft.body = (
            self.query_one("#first").value
            + "\n"
            + self.query_one("#second").value
            + "\n"
            + self.query_one("#third").value
            + "\n"
            + self.query_one("#fourth").value
        )
        for i in range(0, len(list_of_emails)):
            participants.append({"name": "", "email": list_of_emails[i]})
        draft.to = participants
        draft.reply_to_message_id = messageid[0]
        try:
            draft.send()
            self.query_one("#email_from").value = ""
            self.query_one("#title").value = ""
            self.query_one("#first").value = ""
            self.query_one("#second").value = ""
            self.query_one("#third").value = ""
            self.query_one("#fourth").value = ""
            messageid.clear()
            participants.clear()
            app.pop_screen()
        except Exception as e:
            print(e.message)

# This commands should not work on this screen
    def action_delete(self) -> None:
        pass

    def action_compose(self) -> None:
        pass

    def action_refresh(self) -> None:
        pass

    def action_reply(self) -> None:
        pass

# We pressing a key
    def action_cancel(self) -> None:
        app.pop_screen()

    def action_send(self) -> None:
        self.send_email()

# We're pressing a button
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "send":
            self.send_email()
        elif event.button.id == "cancel":
            app.pop_screen()

# Compose screen. This screen we will be displayed when we are
# creating or composing a new email
class ComposeEmail(Screen):
# Setup the bindings for the footer	
    BINDINGS = [
        Binding("r", "refresh", "Refresh", show=False),
        Binding("s", "send", "Send"),
        Binding("c", "cancel", "Cancel"),
        Binding("d", "delete", "Delete", show=False),
        Binding("o", "compose", "Compose Email", show=False),
        Binding("p", "reply", "Reply", show=False),
    ]

# Load up the main components of the screen
    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield Input(placeholder="Email To", id="email_to")
        yield Input(placeholder="Title", id="title")
        yield Label("======================")
        yield Input(id="first")
        yield Input(id="second")
        yield Input(id="third")
        yield Input(id="fourth")
        yield Horizontal(
            Button("Send!", variant="primary", id="send"),
            Label(" "),
            Button("Cancel", variant="primary", id="cancel"),
        )

# Grab the information and send the email
    def send_email(self) -> None:
        participants = []
        draft = nylas.drafts.create()
        list_of_emails = self.query_one("#email_to").value.split(";")
        draft.subject = self.query_one("#title").value
        draft.body = (
            self.query_one("#first").value
            + "\n"
            + self.query_one("#second").value
            + "\n"
            + self.query_one("#third").value
            + "\n"
            + self.query_one("#fourth").value
        )
        for i in range(0, len(list_of_emails)):
            participants.append({"name": "", "email": list_of_emails[i]})
        draft.to = participants
        try:
            draft.send()
            self.query_one("#email_to").value = ""
            self.query_one("#title").value = ""
            self.query_one("#first").value = ""
            self.query_one("#second").value = ""
            self.query_one("#third").value = ""
            self.query_one("#fourth").value = ""
            participants.clear()
            app.pop_screen()
        except Exception as e:
            print(e.message)

# This commands should not work on this screen
    def action_delete(self) -> None:
        pass

    def action_compose(self) -> None:
        pass

    def action_refresh(self) -> None:
        pass

    def action_reply(self) -> None:
        pass

# We pressing a key
    def action_cancel(self) -> None:
        app.pop_screen()

    def action_send(self) -> None:
        self.send_email()

# We pressing a button
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "send":
            self.send_email()
        elif event.button.id == "cancel":
            app.pop_screen()

# Pass the main class and run the application
if __name__ == "__main__":
    app = EmailApp()
    app.run()
