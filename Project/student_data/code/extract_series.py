#!/usr/bin/env python

import os
import pandas as pd

USR_PRDCT_ID = 'user_product_id'
DATE = 'DOKDATUM'
ART_NR = 'ARTNR'
PRICE = 'UTPRIS'
NUMBER = 'ANTAL'
LABEL = 'label'
CHURN_DIR = 'churned'
NONCHURN_DIR = 'not_churned'


def setup_path(out_folder, label):
    '''Create output path

    Parameters
    ----------
    out_folder : Root folder for time series
    label : Current label

    Returns
    -------
    Path to appropriate label dir

    '''
    folder = CHURN_DIR if label is True else NONCHURN_DIR
    path = os.path.join(out_folder, folder)

    if not os.path.exists(path):
        os.mkdir(path)

    return path


def get_price_changes(data):
    '''For every article, get list of times when a price changed to which value

    Parameters
    ----------
    data : Product table

    Returns
    -------
    Dictionary with article : [(date, price)]

    '''
    price_changes = {}
    articles = data[ART_NR].unique()

    for article in articles:
        selected = data[data[ART_NR] == article].sort_values(DATE)
        # get the rows at which the price changes
        change_rows = selected[selected[PRICE].diff() != 0]
        price_changes[article] = [(row[DATE], row[PRICE])
                                  for _, row in change_rows.iterrows()]

    return price_changes


def merge_dates(extracted):
    '''Merge duplicated dates

    Parameters
    ----------
    extracted : Extracted user-product table

    Returns
    -------
    DataFrame without duplicated dates

    '''
    # find duplicated dates
    duplicated_dates = extracted[extracted[DATE].duplicated()][DATE]
    duplicated_dates = duplicated_dates.unique()

    # merge orders
    for date in duplicated_dates:
        date_rows = extracted[extracted[DATE] == date]
        number = date_rows[NUMBER].sum()
        indices = date_rows.index
        extracted.at[indices[0], NUMBER] = number
        # mark all but one duplicate row for deletion
        for idx in indices[1:]:
            extracted.at[idx, NUMBER] = pd.NaT

    extracted.loc[extracted[NUMBER] == 0, NUMBER] = pd.NaT

    return extracted.dropna(subset=[NUMBER])


def add_padding(extracted, price_changes):
    '''Add entries with zero demand to fulfil window_size

    Parameters
    ----------
    extracted : Extracted user-product table
    price_changes : Mapping between data of price change and new price

    Returns
    -------
    DataFrame with padded data

    '''
    # create one row per day
    if not extracted[DATE].is_unique:
        extracted = merge_dates(extracted)
    extracted.index = pd.DatetimeIndex(extracted[DATE])
    padded = extracted.asfreq(freq='D', method='pad')
    padded = padded.drop(columns=[DATE])

    # reset order number
    padded.loc[~padded.index.isin(extracted[DATE]), NUMBER] = 0

    # set price changes
    art_nr = extracted[ART_NR].iloc[0]
    for date, price in price_changes[art_nr]:
        padded.loc[padded.index >= date, PRICE] = price

    return padded


def extract_ts(data, user_product_id, pad, price_changes):
    '''Extract user-product combination and add padding if required

    Parameters
    ----------
    data : Product table
    user_product_id : User-product id to extract
    pad : Indicate if day padding should be used
    price_changes : Mapping between date of price change and new price

    Returns
    -------
    DataFrame containing the extracted data

    '''
    extracted = data[data[USR_PRDCT_ID] == user_product_id].sort_values(DATE)
    if pad is True:
        extracted = add_padding(extracted, price_changes)

    return extracted


def main(csv_file, label_file, out_folder, pad):
    '''Extract user-product combinations into separate CSV files and add
       padding if required

    Parameters
    ----------
    csv_file : Input CSV file
    label_file : Label file
    out_folder : Root folder for time series
    pad : Indicate if day padding should be used

    '''
    data = pd.read_csv(csv_file)
    # convert order dates into date objects
    data[DATE] = pd.to_datetime(data[DATE])

    labels = pd.read_csv(label_file)

    if pad is True:
        price_changes = get_price_changes(data)
    else:
        price_changes = None

    for _, row in labels.iterrows():
        target_path = setup_path(out_folder, row[LABEL])
        tmp_data = extract_ts(data, row[USR_PRDCT_ID], pad,
                              price_changes)
        file_path = os.path.join(target_path,
                                 '{}.csv'.format(row[USR_PRDCT_ID]))
        tmp_data.to_csv(file_path)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Extract user-product time '
                                     'series and store them in folder '
                                     'structure')
    parser.add_argument('csv_file', help='Input CSV file')
    parser.add_argument('label_file', help='Label CSV file')
    parser.add_argument('out_folder', help='Root folder for time series')

    parser.add_argument('--pad', help='Add day-wise padding',
                        action='store_true')

    args = vars(parser.parse_args())
    main(**args)
