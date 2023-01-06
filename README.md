# personal-finance-tracker

Overview:

This is an application developed in python to summarize and visualize the income and expense related data of a person.

Requirements:

The application requires the following python packages to be installed prior to execution.

beautifulsoup
imaplib
pandas
email
numpy
googlemaps
datetime

The application works by crawling the mailservers to identify and extract financial information from the email notifications that a user receives from their bank when a financial transaction is performed. The financial transactions may be performed using a Credit card (VISA/Mastercard) or using a chequing account via Interac/Debit card. So, for the application to work the email notification facility of the bank needs to be enabled (usually done via online banking).

This is the first release of the application and it currently supports only GMAIL addresses and two banks - ScotiaBank and Royal Bank of Canada(RBC).

For the GMAIL mailserver access, you need to create and provide the GMAIL app password. The procedure for this is available in the below link.
https://support.google.com/accounts/answer/185833?hl=en
 
The financial information extracted from the email notifications is enriched by adding information about the businesses where the financial transaction was performed. This is achieved using Google Maps 'Places' API. For the application to work, you will require an API key (can be created on Google Cloud).

Using the application:

Since it is a Python application, it can be executed using the below command.

"python pfa.py"

Please note that depending on the machine where the application file (pfa.py) is executed and the python installation in it, the afore-mentioned command may vary. For example, it can be as shown below.

"C:\ProgramData\Anaconda3\python.exe pfa.py"

The application will prompt for GMAIL ids, GMAIL app passwords, Google API key, start date and end date.

Output of the application:

The application generates a comma-separated file named 'pfa.csv'. This file can be fed as input to the Power BI file 'pfa.pbix' to visualize the income and expense details (you may have to change the source details of the csv file in Power Query).
