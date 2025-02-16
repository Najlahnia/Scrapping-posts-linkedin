import re
import datetime
from dateutil.relativedelta import relativedelta

def get_actual_date(date):
    today = datetime.today().strftime('%Y-%m-%d')
    current_year = datetime.today().strftime('%Y')
    
    def get_past_date(days=0, weeks=0, months=0, years=0):
        date_format = '%Y-%m-%d'
        dtObj = datetime.strptime(today, date_format)
        past_date = dtObj - relativedelta(days=days, weeks=weeks, months=months, years=years)
        past_date_str = past_date.strftime(date_format)
        return past_date_str

    past_date = date
    
    if 'hour' in date:
        past_date = today
    elif 'day' in date:
        date.split(" ")[0]
        past_date = get_past_date(days=int(date.split(" ")[0]))
    elif 'week' in date:
        past_date = get_past_date(weeks=int(date.split(" ")[0]))
    elif 'month' in date:
        past_date = get_past_date(months=int(date.split(" ")[0]))
    elif 'year' in date:
        past_date = get_past_date(months=int(date.split(" ")[0]))
    else:
        split_date = date.split("-")
        if len(split_date) == 2:
            past_month = split_date[0]
            past_day =  split_date[1]
            if len(past_month) < 2:
                past_month = "0"+past_month
            if len(past_day) < 2:
                past_day = "0"+past_day
            past_date = f"{current_year}-{past_month}-{past_day}"
        elif len(split_date) == 3:
            past_month = split_date[0]
            past_day =  split_date[1]
            past_year = split_date[2]
            if len(past_month) < 2:
                past_month = "0"+past_month
            if len(past_day) < 2:
                past_day = "0"+past_day
            past_date = f"{past_year}-{past_month}-{past_day}"

    return past_date



def convert_abbreviated_to_number(s):
    if 'K' in s:
        return int(float(s.replace('K', '')) * 1000)
    elif 'M' in s:
        return int(float(s.replace('M', '')) * 1000000)
    else:
        return int(s)

def clean_date(date_str):
    """Nettoie la chaîne de date pour ne garder que l'heure ou la date."""
    if not date_str or date_str == "No Content":
        return "Unknown"
    cleaned_date = re.sub(r"•\s*Modifié\s*•", "", date_str).strip()
    return cleaned_date