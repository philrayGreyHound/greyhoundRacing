# Import packages
from datetime import datetime

import jsonpath
import pandas as pd
import requests
from tqdm import tqdm

tqdm.pandas()
today_date = datetime.now().strftime("%Y-%m-%d")
races = pd.DataFrame()
dogs = pd.DataFrame()


# Get races
def get_races():
    first_url = 'https://greyhoundbet.racingpost.com/meeting/blocks.sd?view=meetings&r_date=' + today_date + \
                '&blocks=header,list'
    all_races_response = requests.get(first_url).json()
    races['trackId'] = jsonpath.jsonpath(all_races_response, '$..items[?(@.isIrish=="")].races..trackId')
    races['trackName'] = jsonpath.jsonpath(all_races_response, '$..items[?(@.isIrish=="")].races..trackName')
    races['raceId'] = jsonpath.jsonpath(all_races_response, '$..items[?(@.isIrish=="")].races..raceId')
    races['raceTitle'] = jsonpath.jsonpath(all_races_response, '$..items[?(@.isIrish=="")].races..raceTitle')
    races['raceDate'] = jsonpath.jsonpath(all_races_response, '$..items[?(@.isIrish=="")].races..raceDate')

    print('\n\nNumber of races is ' + str(races.shape[0]))


# Get dogs from races
def get_dogs_from_races(x):
    global dogs
    dogs_urls = 'https://greyhoundbet.racingpost.com/card/blocks.sd?track_id=' + x['trackId'] + '&race_id=' \
                + x['raceId'] + '&r_date=' + today_date \
                + '&tab=card&blocks=card-header,card-pager,card-tabs,card-title,card'
    dd = requests.get(dogs_urls).json()
    race_dogs = pd.DataFrame()
    race_dogs['dogId'] = jsonpath.jsonpath(dd, '$.card.dogs..dogId')
    race_dogs['raceId'] = jsonpath.jsonpath(dd, '$.card-tabs.raceId')[0]
    race_dogs['dogName'] = jsonpath.jsonpath(dd, '$.card.dogs..dogName')
    race_dogs['trackName'] = jsonpath.jsonpath(dd, '$.card-tabs.trackName')[0]
    race_dogs['raceTitle'] = jsonpath.jsonpath(dd, '$.card-title.raceTitle')[0]
    race_dogs['raceTime'] = jsonpath.jsonpath(dd, '$.card-tabs.raceDateTime')[0]
    race_dogs['trapNum'] = jsonpath.jsonpath(dd, '$.card.dogs..trapNum')

    dogs = dogs.append(race_dogs)


# Get dogs history
def get_dog_history(x):
    #     global dogs

    dog_history_url = 'https://greyhoundbet.racingpost.com/dog/blocks.sd?race_id=' + x.raceId + \
                      '&r_date=' + today_date + '&dog_id=' + x.dogId + '&blocks=header,details'
    dr = requests.get(dog_history_url).json()
    dog_history = pd.DataFrame()

    dog_history['rOutcomeId'] = jsonpath.jsonpath(dr,
                                                  '$.details.forms..[?(@.rGradeCde && @.rOutcomeDesc!="NR")].rOutcomeId')
    dog_history.rOutcomeId = pd.to_numeric(dog_history.rOutcomeId, errors='coerce')
    dog_history.dropna(inplace=True)

    if dog_history.shape[0] >= 10:
        l10123mean = dog_history.rOutcomeId.iloc[:10].apply(lambda i: i in [1, 2, 3]).mean()
        if l10123mean >= .8:
            top3_last10_races = l10123mean
            first_last10_races = dog_history.rOutcomeId.iloc[:10].apply(lambda i: i == 1).mean()
            second_last10_races = dog_history.rOutcomeId.iloc[:10].apply(lambda i: i == 2).mean()
            third_last10_races = dog_history.rOutcomeId.iloc[:10].apply(lambda i: i == 3).mean()

        else:
            top3_last10_races = first_last10_races = second_last10_races = third_last10_races = float('NAN')

    else:
        top3_last10_races = first_last10_races = second_last10_races = third_last10_races = float('NAN')

    return top3_last10_races, first_last10_races, second_last10_races, third_last10_races


if __name__ == '__main__':
    get_races()

    print('\n')
    print('=' * 100)
    print('Get list of dogs for each race')
    print('=' * 100)

    races.progress_apply(get_dogs_from_races, axis=1)
    dogs.reset_index(inplace=True)
    dogs.drop('index', axis=1, inplace=True)

    print('\n\nNumber of dogs is ' + str(dogs.shape[0]))
    print('\n')
    print('=' * 100)
    print('Get dogs racing history')
    print('=' * 100)

    dogs['top3Last10Races'], dogs['1stLast10Races'], dogs['2ndLast10Races'], dogs['3rdLast10Races'] = zip(
        *dogs.progress_apply(get_dog_history, axis=1))

    dogs.dropna().drop(['dogId', 'raceId'], axis=1).sort_values(by='raceTime').to_csv(
        './reports/greyhound_' + today_date + '.csv',
        index=False)

    print('\n\nNumber of selected dogs is ' + str(dogs.dropna().shape[0]))
