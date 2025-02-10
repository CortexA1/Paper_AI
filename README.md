This app has a login / register function 
or alternative it can get started in the demo mode without any user credentials.

# Technical Set up
1. Set up environment
- python3 -m venv venv
2. Activate venv
- source venv/bin/activate
3. Install dependencies
- pip install -r requirements.txt

# Set up the project
1. Create a file in ".streamlit" folder named "secrets.toml"
2. Add the following secrets (auth_token is used for hashing):
 - db_name="/var/data/paperai.db" (For SQLite database, enter path and the name)
 - auth_token="xx" 
 - free_modus_document_api="xx" (Die Free Keys für die API, Demo & Basis Modus)
 - free_modus_document_key="xx" (Die Free Keys für die API, Demo & Basis Modus)
 - premium_document_api="xx" (Die Premium Keys für die Premium User)
 - premium_document_key="xx" (Die Premium Keys für die Premium User)
 - document_classifier_model="xx" (Classifier Model Name)
 - admin_user="xx" (Enter the name of the user account who should have admin rights, access to monitoring page)
3. Optional: Create Debug settings file specified for your IDE

# PandasAI Installation
## OLD Installing requirements for pandasai
1. Python >= 3.9
2. pandasai==1.4.10 (BaseCallback error in neueren Versionen)

## NEW Installing requirements for pandasai
1. Python (most up to date)
2. pandasai (most up to date)
- Manually Installation of Library 'eval' and 'seaborn', Heatmap can be generated successful now
- Whitelisting of "ast"

# Updating the project
1. Build requirements file
- pip freeze > requirements.txt
2. Creating commit and push to git
- git add .
- git commit -m "Your message"
- git push

