# verification-serive


## HowItWorks

### /verification/sendCode/sms/ api for send sms code
Send phone_number if data is valid, you will receive verification_state

### /verification/checlCode/sms/ api for check code from sms
Send verification_state and code for check if data is ok you'll get http200 otherwise, http400 and error message


#### And the phone_number with state saves as verified and you can use only once this credentials for another api


## ToDo

- [ ] write tests
- [ ] email verification logic and api as sms
- [ ] fix: readme
- [ ] check for all possible hacks
