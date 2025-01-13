### Installation Requirements
- Python and the ability to install modules using pip. This will be automatic through the requirements file.
- A file path for the output of the process, on Windows this might be C:\data\hta\ 
  on Mac/Linux it will be `/home/user/data/hta` or similar where `user` is your account name
- You require an hl7.confluence.org account to use this script and a [Personal Access Token](https://confluence.atlassian.com/enterprise/using-personal-access-tokens-1026032365.html) to HL7 confluence.
- The personal access token value needs to be copied into a file in the root folder of this application. The file must be called `access.token`
- Ensure your confluence account can read the [External Terminologies](https://confluence.hl7.org/display/TA/External+Terminologies+-+Information) page and the child pages
- Ensure any pages you scrape use the standard HTA Confluence template - working examples shown below. 

### How to install this script 
   * `git clone https://github.com/mjosborne1/hta_make_codesys.git`
   * `cd hta_make_codesys`
   * `virtualenv .venv`
   * `source ./.venv/bin/activate`
   * `pip install -r requirements.txt`


### How to run this script
 ```
    usage: main.py [-h] [-d CSDIR] [-n NAME] [-p PAGE]

    options:
    -h, --help               show this help message and exit
    -d CSDIR, --csdir CSDIR  local CodeSystem data folder
    -n NAME, --name NAME     CodeSystem name
    -p PAGE, --page PAGE     Confluence page id
 ```

### Questions
  * Q. Where do I get the page id from?
  * A. If you can see the external terminologies pages, click on the one you want to create a code system for example: [HGVS](https://confluence.hl7.org/display/TA/HGVS). If the page id is not displayed in the url bar of your browser, click on the elipsis (top right) and click 'page information'. The pageId will be displayed in the url bar of your browser. e.g. https://confluence.hl7.org/pages/viewinfo.action?pageId=82905383 
  * Q. What should I put in the CodeSystem name?
  * A. The CodeSystem name is used for naming the XML output file and should match 'Short name or abbreviation of the code system name' in the confluence page.
  * Q. Where does the XML output file go?
  * A. It will be exported to the folder you have used in the --CSDIR or -d parameter, which defaults to `/home/user/data/hta` on Mac, WSL or Linux, where `user` is your user code. On Windows it defaults to `C:\Users\USERNAME\data\hta` where `USERNAME` is your windows user name. Note, This script has not been tested on Windows. You are welcome to fork it, make changes and do a PR against the original repo.
  

### Examples
  * `python main.py --name "211HSIS" --page 94654951 --csdir C:\Temp`
  * `python main.py --name "GenotypeOntology" --page 94637084`

### Quality Report
   The script does a quality report to standard out. If there are no warnings or errors it will just say.
   `QC Reported 0 warnings/errors.` 
   
   Otherwise it will list the missing data elements.
   example:
   ```
    Warning: The required field 'title' is missing or empty.
    Warning: The required field 'description' is missing or empty.
    Warning: The required field 'short_name' is missing or empty.
    Warning: The required field 'pub_date' is missing or empty.
    QC Reported 4 warnings/errors.
   ```

### Regenerating the requirements.txt file
If you change this code and want to regenerate the requirements use this:
   `pip freeze >| requirements.txt`
