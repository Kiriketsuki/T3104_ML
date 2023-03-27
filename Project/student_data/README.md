# Göhlins Student Data

## Data

`cleaned.csv` - anonymized raw data (note that the data uses ',' for decimal
              numbers. This means you need to add `decimal=,` when reading the
              csv file in pandas)
`final.csv` - order data grouped by customer and product (for convenience, a
            combined index: `user_product_id` was added to access each customer-product
            combination; Furthermore, customer-product pairs with less than 10
            orders were removed)
`labels.csv` - mapping of `user_product_id`s to churn label (True for churned,
             False for not churned; A customer-product pair is considered
             churned if it did not occur within 365 days from the last recorded
             order in the dataset or from the last occurrence of the product in
             the dataset)
`without_padding` - CSV files for each `user_product_id` grouped into the
                  folders churned/not_churned - only order events are recorded
`with_padding` - CSV files for each `user_product_id` grouped into the
               folders churned/not_churned - days in between orders were added

## Code

`label.py` - script to create `final.csv` and `labels.csv` from `cleaned.csv`
           (possible to change the churn and inclusion threshold)
`extract_series.py` - script to create the separated time series in
                    `without_padding` and `with_padding` (possible to
                    enable/disable padding)

Run scripts in your Anaconda console:
    `$> python label.py --help`
    `$> python extract_series.py --help`
