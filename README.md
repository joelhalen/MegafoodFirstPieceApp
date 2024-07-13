# MegaFoodFirstPieceApp
- This is a program intended to be used by operators in the pressing department at MegaFood, during the process of performing first piece checks.


## Installation
  1. Clone this repository
  2. Modify example_config.cfg, enter your settings & save as config.cfg
  3. Run `pip install -r requirements.txt` in the working directory of the project
  4. Run `main.py`

## Usage
1. Once the program is running, sign-in using the credentials you were provided. If you need sign-on credentials, contact a member of IT.
2. Select which blend you are inspecting
3. Upload the current image of the lot you are inspecting
4. Compare the previous lots to your current lot to ensure their consistency
5. Press **Confirm** once you're sure the blend matches its predecessors.
6. That's it! Don't forget to sign out of the program afterwards.

 ## Updating product information
  You can update the stored data in your database using the `blend_info.csv` file in the working directory.
  This should be an exact copy of the **Product Information** spreadsheet from MegaFood's Weekly Dashboard (hidden sheet).
These updates should only need to take place when significant changes are made to any blend(s).


Designed by Andy Morris
andy@joelhalen.net
