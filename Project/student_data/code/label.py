#!/usr/bin/env python

import datetime as dt
import pandas as pd

CHURNED = 1
NOT_CHURNED = 0
USR_PRDCT_ID = 'user_product_id'
ART_NR = 'ARTNR'
LABEL = 'label'
DATE = 'DOKDATUM'
NUMBER = 'ANTAL'


def infer_threshold(data, art_nr, date_threshold, churn_threshold):
    '''Determine after which date we consider a user-product combination
       churned.
       In general, this date is given by date_thresh, but if a product was
       discontinued, this threshold should be adjusted. We determine if a
       product was discontinued by checking if someone else orderd it within
       date_thresh. Otherwise, we use the last oder date minus churn_threshold
       as new threshold.

    Parameters
    ----------
    data : Product table
    art_nr : Article number
    date_threshold : Default threshold
    churn_threshold : Number of days after which user-product is considered

    Returns
    -------
    Adjusted threshold

    '''
    article_orders = data[data[ART_NR] == art_nr]
    latest_order = article_orders[DATE].max()

    if latest_order > date_threshold:
        threshold = date_threshold
    else:
        threshold = latest_order - dt.timedelta(days=churn_threshold)

    return threshold


def infer_labels(data, churn_threshold, inclusion_threshold):
    '''Infer labels for every user-product id, which qualifies based on
    inclusion_threshold

    Parameters
    ----------
    data : Product table
    churn_threshold : Number of days after which user-product is considered
    inclusion_threshold : Number of order events required to include
                          user-product id

    Returns
    -------
    DataFrame of user-product ids and labels

    '''
    labels = {USR_PRDCT_ID: [], LABEL: []}
    article_thresholds = {}

    # get date after which an order must have been placed to be considered
    # churned
    most_recent = data[DATE].max()
    date_thresh = most_recent - dt.timedelta(days=churn_threshold)

    for id in data[USR_PRDCT_ID].unique():
        occurrences = data[data[USR_PRDCT_ID] == id]
        if len(occurrences) < inclusion_threshold:
            continue
        labels[USR_PRDCT_ID].append(id)

        # infer article specific time threshold
        art_nr = occurrences[ART_NR].iloc[0]
        if art_nr not in article_thresholds:
            article_thresholds[art_nr] = infer_threshold(data, art_nr,
                                                         date_thresh,
                                                         churn_threshold)

        # consider churned, if there was no order after the determined article
        # specific time threshold
        labels[LABEL].append(not (occurrences[DATE]
                             > article_thresholds[art_nr]).any())

    return pd.DataFrame(labels)


def main(csv_file, data_file, label_file, churn_threshold,
         inclusion_threshold):
    '''Add user-product id for every user-product combination and create
       mapping of user-product ids to churned/not-churned

    Parameters
    ----------
    csv_file : Cleanded CSV file
    data_file : Output CSV file with added user-prduct ids
    label_file : Mapping of user-product ids to labell
    churn_threshold : Number of days after which user-product is considered
                      churned
    inclusion_threshold : Number of order events required to include
                          user-product id

    '''
    data = pd.read_csv(csv_file, decimal=',')

    # convert order dates into date objects
    data[DATE] = pd.to_datetime(data[DATE])

    # add user-product id column
    data.insert(loc=0, column=USR_PRDCT_ID,
                value=data.set_index(['KUNDNR', 'ARTNR']).index.factorize()[0]+1)
    # remove orders with product number zero
    data = data[data[NUMBER] != 0]

    labels = infer_labels(data, churn_threshold, inclusion_threshold)

    # filter out ignored user-product ids
    data = data[data[USR_PRDCT_ID].isin(labels[USR_PRDCT_ID])]

    data.to_csv(data_file, index=False)
    labels.to_csv(label_file, index=False)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Create list of churned '
                                     'user-product combinations.')
    parser.add_argument('csv_file', help="Cleaned CSV file")
    parser.add_argument('data_file', help="Updated CSV file")
    parser.add_argument('label_file', help="Mapping of user-product ids to "
                        "label (churned: True, not churned: False)")

    parser.add_argument('--churn_threshold', help='Number of days after '
                        'which user-product combination is considered churned',
                        type=int, default=365)
    parser.add_argument('--inclusion_threshold', help='User-product '
                        'combination needs to have at least threshold many '
                        'occurrences', type=int, default=10)

    args = vars(parser.parse_args())
    main(**args)
