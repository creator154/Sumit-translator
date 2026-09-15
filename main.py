import time, os, platform
import sys

try:
    from prettytable import PrettyTable
except:
    os.system("pip install prettytable")
    from prettytable import PrettyTable

rd, gn, lgn, yw, lrd, be, pe = '\033[00;31m', '\033[00;32m', '\033[01;32m', '\033[01;33m', '\033[01;31m', '\033[94m', '\033[01;35m'
cn, k, g = '\033[00;36m', '\033[90m', '\033[38;5;130m'

def re(text):
    for char in text:
        print(char, end='', flush=True)
        time.sleep(0.001)  

if 'Windows' in platform.uname():
    from colorama import init
    init()

banner = f"""
                                                                 
{k}                                                                
                              -     -                            
                            .+       +.                          
                           :#         #:                         
                          =%           %-                        
   {lrd} Telegram {k}  -{g} Jay Ghunawat{k}   .%+    {be} Max Reporter   {k}       
                        #@:             -@#                      
                     :  #@:             :@*  :                   
                    -=  *@:             -@*  =-                  
                   -%   *@-             =@+   %-                 
                  -@=  .*@+             +@+.  =@-                
                 =@%   .+@%-    :.:    -@@+.   #@:               
                =@@#:     =%%-+@@@@@+-%%=     .#@@=              
                 .+%@%+:.   -#@@@@@@@#-   .:=#@%=                
                    -##%%%%%#*@@@@@@@*#%%%%%##-                  
                  .*#######%@@@@@@@@@@@%#######*.                
               .=#@%*+=--#@@@@@@@@@@@@@@@#--=+*%@#=.             
            .=#@%+:     *@@@@@+.   .+@@@@@*     :+%@#=.          
          :*@@=.    .=#@@@@@@@       @@@@@@@#=.    .=@@*.        
            =@+    .%@@*%@@@@@*     *@@@@@%*@@%.    +@=          
             :@=    +@# :@@@@@#     #@@@@%. #@+    =@:           
              .#-   :@@  .%@@#       #@@#.  @@:   -#.            
                +:   %@:   =%         %=   :@%   -+              
                 -.  +@+                   +@+  .-               
                  .  :@#                   #@:  .                
                    @{cn}@Mannucybersecurity{k}@%                    
                      :+@:               =@+:                    
                        =@:             :@-                      
                         -%.           .%:                       
                          .#           #.                        
                            +         +                          
                             -       -                     
"""

re(banner)
re("Warning ! This is a test reporter, any offense is the responsibility of the user !\n")
print(f"{lrd}")

t = PrettyTable([f'{cn}Number{lrd}', f'{cn}info{lrd}'])
t.add_row([f'{lgn}1{lrd}', f'{gn}Reporter Channel{lrd}'])
t.add_row([f'{lgn}2{lrd}', f'{gn}Reporter Account{lrd}'])
t.add_row([f'{lgn}3{lrd}', f'{gn}Reporter Group [Updating]{lrd}'])
print(t)

# --- यहाँ फ़िक्स किया गया है ---
# Heroku पर input() नहीं चलेगा, इसलिए हम Environment Variable का इस्तेमाल करेंगे।
# अगर कोई वेरिएबल नहीं सेट होगा, तो यह डिफ़ॉल्ट रूप से "2" चुन लेगा।
number = os.environ.get("REPORTER_CHOICE", "2")
print(f"{gn}Selected Number (from env): {cn}{number}\n")

if number == "1":
    os.system("python report/reporter.py")
elif number == "2":
    os.system("python report/report.py")
elif number == "3":
    print("This section is being updated and will be added soon \n\nChannel :@Mannucybersecurity")
else:
    print(f"{rd}Invalid selection: {number}")
