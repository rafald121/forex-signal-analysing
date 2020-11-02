## Forex's signal analyse engine

It is code from 05.2019 but I recently pushed it to public GitHub repository for recruitment process. 

Most of engine's logic is in `app/backtest/` module. 

I know that a lot of project's code could be written better but It was 1.5 years ago from now(2020.11) and I learnt a lot new things since this moment.

## Description
It is my engineer thesis in which I tried to analyse signals messages (buy or sell decision suggestions messages) effectiveness based on historical Forex prices and Telegram forex signals authors' messages.
To achieve this I had to create engine that:
1. retrieving, scrapping and storing historical currency prices
2. parsing and analysing signal messages
3. imitating of buy and sell flow for some period of time for given amount of messages at the time
4. creating reports of effectiveness for given signal authors, for given period of time or given currency

Used technologies:
- Python
- MongoDB with mongoengine ORM
- Docker
- Jupyter notebook
- Selenium
- pandas
- Regular expressions
