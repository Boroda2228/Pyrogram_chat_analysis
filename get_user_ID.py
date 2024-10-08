from pyrogram import Client
from pyrogram.types import InputPhoneContact
import json
import tempfile

api_id = ########
api_hash = ""
app = Client("number", api_id=api_id, api_hash=api_hash)

def get_chat_id(phone_num):
    temp_contact_name = tempfile.NamedTemporaryFile().name.split('\\')[-1]
    good_res = []
    
    with app:
        app.import_contacts([InputPhoneContact(phone=phone_num, first_name=temp_contact_name)])
        contacts = app.get_contacts()
        
        for contact in contacts:
            contact_data = json.loads(str(contact))
            if contact_data['first_name'] == temp_contact_name:
                good_res.append(contact_data)
                app.delete_contacts(contact_data['id'])
                
        try:
            good_res = good_res[0]['id']
        except IndexError:
            good_res = None
            
    return good_res

print(get_chat_id('+79991234455'))
