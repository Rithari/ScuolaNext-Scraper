# About
ArgoSoftware's ScuolaNext Family Portal provides students with assignments / homework.
Unfortunately, though, not everyone has the ability to access the platform freely. 
This project aims to bring the assignments given by teachers to all students within a class, easily, by posting it to a WhatsApp group!

## How does it work?
It's simple. The script is written in Python and uses Selenium to navigate to the assignments automatically and scrape the data from them.
Since the file downloads are exclusive to logged-in users, the script downloads the files and uploads them to a file hosting service, making it accessible to anyone. 
Afterwards, the refined data will be sent to a database for storing purposes and then shipped off to a WhatsApp group.

# Usage
You need to add a `config.ini` file your running directory. The file must be structured as follows: 
```
[main]
utente =
password =
codice_scuola =
download_dir =
group_name =
key =
```
#### Important
* `download_dir` must have double slashes, for example: `C:\\Users\\Rithari\\Documents\\argo\\`
* `Group_Name` is the whatsapp group name
* `Key` is the upload key of the file hosting service

Selenium uses the 'chrome driver', which you might need to download separately. Check your current's browser's version (chrome) and download its respective webdriver, placing it in the same directory as the script.
Upon running it for the first time, two folders will appear in your directory, for the two driver profiles which are needed to keep you authenticated. 
Keep your WhatsApp Web scanner on hand, if you don't manage to scan the QR code in time, the program will crash. Simply scan it and re run the script should you fail the first time. 



# Notes
I do not provide any type of support for this project, it is a hobby project I have come up with to help my classmates and also to further my understanding of Python and web scraping.
If you believe something is broken and there isn't an issue about it yet, please make one! 
I know this isn't the best kind of software you have ever seen, but it was never meant for distribution or for perfect conventions.

Thank you!
