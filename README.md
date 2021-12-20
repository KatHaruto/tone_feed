# tone_feed
sensor applicatoin.


## setup
Clone this repository.
```
git clone https://github.com/tr-author/tone_feed.git
```

Create environment via pipenv.  
Install pipenv using following command if you don't have it.

```pip install pipenv```

```pipenv install```

## Run
Be sure to wear eaphones.


```pipenv run python main.py -p <note>```  
```pipenv run python main.py -p C3```
  
The voice from the input is processed and output as it is from one earphone and pitch corrected from the other.  
with p option, you can specify the corrected pitch like C,D,D#,A♭2.
