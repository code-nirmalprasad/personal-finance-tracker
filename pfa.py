import imaplib
import datetime
import email
from bs4 import BeautifulSoup as bs
import pandas as pd
import numpy as np
import googlemaps

sb_gmail_id = input("Enter GMAIL address registered with ScotiaBank: ")
sb_gmail_pass = input("Enter app password for afore-mentioned GMAIL address registered with ScotiaBank: ")
rbc_gmail_id = input("Enter GMAIL address registered with Royal Bank of Canada(RBC): ")
rbc_gmail_pass = input("Enter app password for afore-mentioned GMAIL address registered with RBC: ")
start_date = input("Enter Start Date (dd-mm-yyyy): ")
end_date = input("Enter End Date (dd-mm-yyyy): ")
api_key = input("Enter Google Maps API key: ")
start_date = start_date.split("-")
start_date_day = int(start_date[0])
start_date_month = int(start_date[1])
start_date_year = int(start_date[2])
end_date = end_date.split("-")
end_date_day = int(end_date[0])
end_date_month = int(end_date[1])
end_date_year = int(end_date[2])

maps_client=googlemaps.Client(api_key)

scotiabank_mailserver = ('imap.gmail.com', sb_gmail_id, sb_gmail_pass)
scotiabank_mailer_list = ["scotiainfoalerts@scotiabank.com", "infoalerts@scotiabank.com", "notify@payments.interac.ca"]
rbc_mailserver = ('imap.gmail.com', rbc_gmail_id, rbc_gmail_pass)
rbc_mailer_list = ["rbcroyalbankalerts@alerts.rbc.com"]
year = datetime.date.today().year
month = datetime.date.today().month
from_date = datetime.date(start_date_year, start_date_month, start_date_day).strftime("%d-%b-%Y")
to_date = datetime.date(end_date_year, end_date_month, end_date_day).strftime("%d-%b-%Y")

def comb_mailserver(mailserver, mailer_list, from_date, to_date, bank):
    host, user, password = mailserver
    conn = imaplib.IMAP4_SSL(host)
    conn.login(user, password)
    conn.select('inbox')
    if bank == 'scotiabank':
        data_list=[]
        for mailer in mailer_list:
            data=comb_scotiabank_mailer(conn, from_date, to_date, mailer)
            data_list.append(data)
        return pd.concat(data_list, axis=0, ignore_index=True)
    elif bank == 'rbc':
        data_list = []
        for mailer in mailer_list:
            data=comb_rbc_mailer(conn, from_date, to_date, mailer)
            data_list.append(data)
        return pd.concat(data_list, axis=0, ignore_index=True)

def comb_rbc_mailer(connection, from_date, to_date, mailer):
    _, search_data = connection.search(None, '(FROM {} SENTSINCE {} SENTBEFORE {})'.format(mailer, from_date, to_date))
    ids = search_data[0]  # data is a list.
    id_list = ids.split()  # ids is a space separated string
    subject_list, to_add_list, from_add_list, date_list, text_list = [], [], [], [], []
    type_list, amount_list, account_list, description_list = [], [], [], []
    bank_list, account_type_list, category_list, sub_category_list = [], [], [], []
    for id in id_list:
        latest_email_id = id_list[0]
        result, data = connection.fetch(id, "(RFC822)")
        _, b = data[0]
        email_message = email.message_from_bytes(b)
        if email_message['subject'] != "Credit Card Bill Due":
            subject_list.append(email_message['subject'])
            to_add_list.append(email_message['to'])
            from_add_list.append(email_message['from'])
            date_list.append(datetime.datetime.strptime(email_message['date'][0:-6], '%a, %d %b %Y %H:%M:%S').date())
            for part in email_message.walk():
                if part.get_content_type() == "text/html":
                    body = part.get_payload(decode=True).decode()
                    soup = bs(body, 'html.parser')
                    table_tags = soup.find_all('table', {'class': 'one-column'})
                    text_list.append(" ".join(table_tags[0].text.split()))
                    type, amount, account, description, bank, account_type, category, sub_category = process_rbc_text(email_message['subject'], table_tags[0].text.split())
                    type_list.append(type)
                    amount_list.append(amount[1:])
                    account_list.append(account)
                    description_list.append(description)
                    bank_list.append(bank)
                    account_type_list.append(account_type)
                    category_list.append(category)
                    sub_category_list.append(sub_category)
    df=pd.DataFrame({'date': date_list, 'from': from_add_list, 'to': to_add_list, 'subject': subject_list, 'text': text_list, 'type': type_list, 'amount': amount_list, 'account': account_list, 'description': description_list, 'bank': bank_list, 'account_type': account_type_list, 'category': category_list, 'sub_category': sub_category_list})
    return df

def process_rbc_text(subject, text):
    if subject == "Withdrawal Warning":
        list1 = ['Hello,', 'A', 'withdrawal', 'of', 'was', 'debited', 'from', 'your', 'The', 'full', 'details', 'of',
                 'this', 'transaction', 'are', 'below:']
        list2 = text
        for word in list1:
            list2.remove(word)
        type = 'Dr'
        amount = list2[0]
        account = " ".join(list2[1:4])
        bank = "RBC"
        account_type = "Bank Account"
        description = " "
        category = " "
        sub_category = get_sub_category(description)
        return(type, amount, account, description, bank, account_type, category, sub_category)
    elif subject == "Deposit Notice":
        list1 = ['Hello,', 'A', 'deposit', 'of', 'was', 'made', 'to', 'your', 'on', 'The', 'full', 'details', 'of', 'this', 'transaction', 'are', 'below:']
        list2 = text
        for word in list1:
            list2.remove(word)
        type = 'Cr'
        amount = list2[0]
        account = " ".join(list2[1:4])
        bank = "RBC"
        account_type = "Bank Account"
        description = " "
        category = " "
        sub_category = get_sub_category(description)
        return (type, amount, account, description, bank, account_type, category, sub_category)
    elif subject == "You made a purchase.":
        list1 = ['Hello,', 'As', 'requested,', 'we’re', 'letting', 'you', 'know', 'that', 'a', 'purchase', 'of', 'was',
                 'made', 'on', 'your', 'RBC', 'Royal', 'Bank', 'on', 'towards', 'If', 'you', 'don’t', 'recognize',
                 'this', 'transaction,', 'please', 'call', 'us', 'at', '1‑800‑769‑2512', '(available', '24/7)', 'and',
                 'we’ll', 'be', 'happy', 'to', 'help.']
        list2 = text
        for word in list1:
            list2.remove(word)
        type = 'Dr'
        amount = list2[0]
        account = " ".join(list2[1:5])
        bank = "RBC"
        account_type = "Credit Card"
        description = " ".join(list2[(list2.index('Description:')+1):])
        category = "Expense"
        sub_category = get_sub_category(description)
        return (type, amount, account, description, bank, account_type, category, sub_category)
    elif subject == "Payment Made":
        list1 = ['Hello,', 'A', 'payment', 'for', 'has', 'been', 'made', 'to', 'your', 'The', 'full', 'details', 'of',
                 'this', 'transaction', 'are', 'below:']
        list2 = text
        for word in list1:
            list2.remove(word)
        type = 'Cr'
        amount = list2[0]
        bank = "RBC"
        account_type = "Credit Card"
        account = " ".join(list2[1:])
        description = " "
        category = " "
        sub_category = get_sub_category(description)
        return (type, amount, account, description, bank, account_type, category, sub_category)
    elif subject == "Credit Card Bill Due":
        pass

def comb_scotiabank_mailer(connection, from_date, to_date, mailer):
    _, search_data = connection.search(None, '(FROM {} SENTSINCE {} SENTBEFORE {})'.format(mailer, from_date, to_date))
    ids = search_data[0]  # data is a list.
    id_list = ids.split()  # ids is a space separated string
    subject_list, to_add_list, from_add_list, date_list, text_list = [], [], [], [], []
    type_list, amount_list, account_list, description_list = [], [], [], []
    bank_list, account_type_list, category_list, sub_category_list = [], [], [], []
    for id in id_list:
        result, data = connection.fetch(id, "(RFC822)")
        _, b = data[0]
        email_message = email.message_from_bytes(b)
        if email_message['subject'] != "e-Statement issued for credit card or line of credit" and email_message['subject'] != "Minimum payment due for credit card or line of credit":
            if email_message['from'] == "Scotiabank <notify@payments.interac.ca>":
                sub=email_message['subject'].split()
                if " ".join(sub[0:6] + sub[-2:]) == "INTERAC e-Transfer: Your money transfer to was deposited.":
                    continue
            subject_list.append(email_message['subject'].replace('\r', '').replace('\n', ''))
            to_add_list.append(email_message['to'])
            from_add_list.append(email_message['from'])
            date_list.append(datetime.datetime.strptime(email_message['date'][0:-6], '%a, %d %b %Y %H:%M:%S %z').date())
            for part in email_message.walk():
                if part.get_content_type() == "text/plain" or part.get_content_type() == "text/html":
                    body = part.get_payload(decode=True).decode()
            soup = bs(body, 'html.parser')
            p_tags = soup.find_all('p')
            text = p_tags[0].text.strip().replace('\r', '').replace('\n', '')
            text_list.append(text)
            type, amount, account, description, bank, account_type, category, sub_category = process_sb_text(email_message['subject'], p_tags[0].text.split())
            type_list.append(type)
            amount_list.append(amount[1:])
            account_list.append(account)
            description_list.append(description)
            bank_list.append(bank)
            account_type_list.append(account_type)
            category_list.append(category)
            sub_category_list.append(sub_category)
    df=pd.DataFrame({'date': date_list, 'from': from_add_list, 'to': to_add_list, 'subject': subject_list, 'text': text_list, 'type': type_list, 'amount': amount_list, 'account': account_list, 'description': description_list, 'bank': bank_list, 'account_type': account_type_list, 'category': category_list, 'sub_category': sub_category_list})
    return df

def process_sb_text(subject, text):
    if subject == "Authorization on your credit account":
        list1 = ['There', 'was', 'an', 'authorization', 'for', 'at', 'on', 'at']
        list2 = text
        for word in list1:
            list2.remove(word)
        type = 'Dr'
        amount = list2[0]
        account = list2[(list2.index('account') + 1):(list2.index('account') + 2)][0]
        bank = "Scotiabank"
        account_type = "Credit Card"
        description = " ".join(list2[1:(list2.index('account'))])
        category = "Expense"
        sub_category = get_sub_category(description)
        return (type, amount, account, description, bank, account_type, category, sub_category)
    elif subject == "Authorization without credit card present":
        list1 = ['There', 'was', 'an', 'authorization', 'without', 'the', 'credit', 'card', 'present', 'for', 'at',
                 'on', 'at']
        list2 = text
        for word in list1:
            list2.remove(word)
        type = 'Dr'
        amount = list2[0]
        account = list2[(list2.index('account') + 1):(list2.index('account') + 2)][0]
        bank = "Scotiabank"
        account_type = "Credit Card"
        description = " ".join(list2[1:(list2.index('account'))])
        category = "Expense"
        sub_category = get_sub_category(description)
        return (type, amount, account, description, bank, account_type, category, sub_category)
    elif subject == "Payment received for your credit card or line of credit":
        list1 = ['A', 'payment', 'of', 'to', 'your', 'was', 'received', 'on', 'For', 'more', 'information,', 'sign',
                 'in', 'to', 'your', 'Scotiabank', 'online', 'or', 'in', 'the', 'mobile', 'app.']
        list2 = text
        for word in list1:
            list2.remove(word)
        type = 'Cr'
        amount = list2[0]
        account = list2[1: (list2.index('account'))][0]
        bank = "Scotiabank"
        account_type = "Credit Card"
        description = " "
        category = " "
        sub_category = get_sub_category(description)
        return (type, amount, account, description, bank, account_type, category, sub_category)
    elif subject == "Interac e-Transfer sent":
        list1 = ['An', 'Interac', 'e-Transfer', 'for', 'was', 'sent', 'using', 'at']
        list2 = text
        for word in list1:
            list2.remove(word)
        type = 'Dr'
        amount = list2[0]
        account = list2[(list2.index('account') + 1):(list2.index('account') + 2)][0]
        bank = "Scotiabank"
        account_type = "Bank Account"
        description = " "
        category = " "
        sub_category = get_sub_category(description)
        return (type, amount, account, description, bank, account_type, category, sub_category)
    elif subject == "Interac Debit transaction":
        list1 = ['Your', 'was', 'used', 'for', 'an', 'Interac', 'Debit', 'transaction', 'of', 'at']
        list2 = text
        for word in list1:
            list2.remove(word)
        type = 'Dr'
        amount = list2[1]
        account = list2[0]
        bank = "Scotiabank"
        account_type = "Bank Account"
        description = " "
        category = " "
        sub_category = get_sub_category(description)
        return (type, amount, account, description, bank, account_type, category, sub_category)
    elif subject == "Bill payment made":
        list1 = ['A', 'bill', 'payment', 'was', 'made', 'for', 'from', 'at']
        list2 = text
        for word in list1:
            list2.remove(word)
        type = 'Dr'
        amount = list2[0]
        account = list2[(list2.index('account') + 1):(list2.index('account') + 2)][0]
        bank = "Scotiabank"
        account_type = "Bank Account"
        description = " "
        category = "Bill Payment"
        sub_category = get_sub_category(description)
        return (type, amount, account, description, bank, account_type, category, sub_category)
    elif " ".join(subject.split()[0:6]+subject.split()[-4:]) == "INTERAC e-Transfer: A money transfer from has been automatically deposited.":
        list1 = ['has', 'sent', 'you', '(CAD)', 'and', 'the', 'money', 'has', 'been', 'automatically', 'deposited',
                 'into', 'your', 'bank', 'account', 'at', 'Scotiabank.']
        list2 = text
        for word in list1:
            list2.remove(word)
        type = 'Cr'
        amount = list2[-1]
        account = " "
        bank = "Scotiabank"
        account_type = "Bank Account"
        description = " "
        category = " "
        sub_category = get_sub_category(description)
        return (type, amount, account, description, bank, account_type, category, sub_category)
    elif " ".join(subject.split()[0:2]+subject.split()[-4:]) == "INTERAC e-Transfer: accepted your money transfer.":
        list1 = ['The', 'money', 'transfer', 'you', 'sent', 'to', 'for', 'the', 'of', '(CAD)', 'was', 'accepted.']
        list2 = text
        for word in list1:
            list2.remove(word)
        type = 'Dr'
        amount = list2[-1]
        account = " "
        bank = "Scotiabank"
        account_type = "Bank Account"
        description = " "
        category = " "
        sub_category = get_sub_category(description)
        return (type, amount, account, description, bank, account_type, category, sub_category)
    elif subject == "e-Statement issued for credit card or line of credit":
        pass
    elif subject == "Minimum payment due for credit card or line of credit":
        pass

def get_sub_category(desc):
    if desc == " ":
        return(" ")
    else:
        response = maps_client.places(query=desc)
        if response['status'] == 'OK':
            resp_text=response['results'][0]['types'][0].replace('_', ' ')
            return(resp_text)
        else:
            return(" ")
print("Crawling mailservers for transaction messages...")
df_sb = comb_mailserver(scotiabank_mailserver, scotiabank_mailer_list, from_date, to_date, 'scotiabank')
print('Scotiabank processing completed.')
df_rbc = comb_mailserver(rbc_mailserver, rbc_mailer_list, from_date, to_date, 'rbc')
print('RBC processing completed.')
print("Processing the transaction messages...")
df = pd.concat([df_sb, df_rbc], axis=0, ignore_index=True)
df.to_csv('temp.csv')
df2 = pd.read_csv('temp.csv')
df2.drop(columns=['Unnamed: 0'], inplace=True)
df2.sort_values(by=['date', 'amount', 'bank'], ignore_index=True, inplace=True)

for index in list(range(df2.shape[0])):
    date=df2.iloc[index,]['date']
    type1=df2.iloc[index,]['type']
    amount=df2.iloc[index,]['amount']
    bank=df2.iloc[index,]['bank']
    account_type=df2.iloc[index,]['account_type']
    category=df2.iloc[index,]['category']
    if account_type == 'Bank Account' and category == " ":
        if type1=='Cr':
            filt=(df2['date']==date) & (df2['type']=='Dr') & (df2['account_type']=='Bank Account') & (df2['amount']==amount) & (df2['category']==" ")
            if df2.loc[filt].shape[0] == 1:
                ind=(df2.loc[filt]).index[0]
                df2.iloc[index, 11] = "Internal Transfer"
                df2.iloc[ind, 11] = "Internal Transfer"
            elif df2.loc[filt].shape[0] == 0:
                df2.iloc[index, 11] = "Income"
        if type1=='Dr':
            filt=(df2['date']==date) & (df2['type']=='Cr') & (df2['account_type']=='Bank Account') & (df2['amount']==amount) & (df2['category']==" ")
            if df2.loc[filt].shape[0] == 1:
                ind=(df2.loc[filt]).index[0]
                df2.iloc[index, 11] = "Internal Transfer"
                df2.iloc[ind, 11] = "Internal Transfer"
            elif df2.loc[filt].shape[0] == 0:
                filt2=(df2['date']==date) & (df2['type']=='Cr') & (df2['account_type']=='Credit Card') & (df2['amount']==amount) & (df2['category']==" ")
                if df2.loc[filt2].shape[0] == 1:
                    ind=(df2.loc[filt2]).index[0]
                    df2.iloc[index, 11] = "Credit Card Payment"
                    df2.iloc[ind, 11] = "Credit Card Payment"
                else:
                    df2.iloc[index, 11] = "Utilities/Third Party Transfer"

df2.to_csv('pfa.csv')
print("Processing completed. Check the file 'pfa.csv'.")
