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
 - db_host="xx"
 - db_user="xx"
 - db_password="xx"
 - db_name="xx"
 - auth_token="xx" 
 - demo_modus=1 (0 is productive)
 - demo_modus_document_api="xx"
 - demo_modus_document_key="xx" 
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