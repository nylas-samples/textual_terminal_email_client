# Import your dependencies
from dotenv import load_dotenv
import os
from rich.text import Text
from nylas import Client
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import DataTable, Label, Header, Footer, Input, Button, TextArea
from textual.screen import Screen
from textual.binding import Binding
from bs4 import BeautifulSoup
import textwrap
from typing import List, Any
from nylas.models.messages import ListMessagesQueryParams
from nylas.models.messages import UpdateMessageRequest

# Load your env variables
load_dotenv()

# Initialize an instance of the Nylas SDK using the client credentials
nylas = Client(
    api_key = os.environ.get("V3_TOKEN")
)

# Create the header of the Data Table
ROWS = [("Date", "Subject", "From", "Unread")]

# Global variables
messageid = []

# Get the body of a particular message clean of HTML tags
def get_message(self, message_id: str) -> str:
    body = ""
    message, _ = nylas.messages.find(os.environ.get("GRANT_ID"), message_id)
    soup = BeautifulSoup(message.body, "html.parser")
    for data in soup(["style", "script"]):
        data.decompose()
    wrapper = textwrap.TextWrapper(width=75)
    word_list = wrapper.wrap(text=" ".join(soup.stripped_strings))
    for word in word_list:
        body = body + word + "\n"
    if message.unread is True:
        request_body = UpdateMessageRequest(unread = False)
        nylas.messages.update(os.environ.get("GRANT_ID"), message_id, request_body)
        self.populate_table()
    return body

# Read the first 5 messages of our inbox
def get_messages() -> List[Any]:
# Create query parameters
    query_params = ListMessagesQueryParams(
        {'in' : "inbox", 'limit': 5}
   )
	
    messages, _, _ = nylas.messages.list(os.environ.get("GRANT_ID"), query_params)
    ROWS.clear()
    ROWS.append(("Date", "Subject", "From", "Unread"))
    for message in messages:
        _from = message.from_[0]['name'] + " / " + message.from_[0]['email']
        ROWS.append(
            (
                message.date,
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
            nylas.messages.destroy(os.environ.get("GRANT_ID"), self.id_message)
            self.populate_table()
        except Exception as e:
            print(e)
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
        body = TextArea(id="body")
        body.show_line_numbers = False
        yield body
        yield Horizontal(
            Button("Send!", variant="primary", id="send"),
            Label(" "),
            Button("Cancel", variant="primary", id="cancel"),
        )

# After we load the components, fill up their data
    def on_mount(self) -> None:
        pass
        message =  nylas.messages.find(os.environ.get("GRANT_ID"), messageid[0]).data
        self.query_one("#body").text = "<br>====<br>" + get_message(self, messageid[0])
        self.query_one("#body").text += "<br><br>Send from my Terminal Email Client" 
        self.query_one("#email_from").value = message.from_[0]['email']
        self.query_one("#title").value = "Re: " + message.subject

# Grab the information and send the reply to the email
    def send_email(self) -> None:
        participants = []
        list_of_emails = self.query_one("#email_from").value.split(";")        
        for i in range(0, len(list_of_emails)):
            participants.append({"name": "", "email": list_of_emails[i]})        
        
        body = {"subject" : self.query_one("#title").value, 
                     "body": self.query_one("#body").text,
                     "to":participants}
        try:
            nylas.messages.send(os.environ.get("GRANT_ID"), request_body = body)
            self.query_one("#email_from").value = ""
            self.query_one("#title").value = ""
            messageid.clear()
            participants.clear()
            app.pop_screen()
        except Exception as e:
            print(e)

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
        body = TextArea(id="body")
        body.show_line_numbers = False
        body.text = "<br><br>Send from my Terminal Email Client"
        yield body
        yield Horizontal(
            Button("Send!", variant="primary", id="send"),
            Label(" "),
            Button("Cancel", variant="primary", id="cancel"),
        )

# Grab the information and send the email
    def send_email(self) -> None:
        participants = []
        list_of_emails = self.query_one("#email_to").value.split(";")
        body = self.query_one("#body").text
        for i in range(0, len(list_of_emails)):
            participants.append({"name": "", "email": list_of_emails[i]})        
        
        body = {"subject" : self.query_one("#title").value, 
                     "body": self.query_one("#body").text,
                     "to":participants}
        try:
            nylas.messages.send(os.environ.get("GRANT_ID"), request_body = body)
            participants.clear()
            app.pop_screen()
        except Exception as e:
            print(e)

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
