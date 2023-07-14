import datetime
import os
import time
import json

try:
    from bs4 import BeautifulSoup
    import lxml
    from selenium.webdriver import ChromeOptions, Chrome
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.common.action_chains import ActionChains
    import selenium.common

except:
    os.system("pip install selenium")
    os.system("pip install bs4")
    os.system("pip install lxml")
    os.system("pip install undetected_chromedriver")

    from bs4 import BeautifulSoup
    import lxml
    from selenium.webdriver import ChromeOptions, Chrome
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.common.action_chains import ActionChains
    import selenium.common

import utils

# I_JSON = {
#     "destination": "Турция",  # ПУНКТ НАЗНАЧЕНИЯ
#     "departure_dates": {  # ДИАПАЗОН ВЫЛЕТА
#         "start_date": "2023-05-29",
#         "end_date": "2023-06-09"
#     },
#     "duration": {  # ПРОДОЛЖИТЕЛЬНОСТЬ ТУРА
#         "min_duration": 4,
#         "max_duration": 9
#     },
#     "board_type": "все включено",  # ПИТАНИЕ
#     "hotel_stars": {  # РЕЙТИНГ ОТЕЛЯ
#         "min_stars": 3.4,
#         "max_stars": 5
#     },
#     "price_range": {  # ДИАПАЗОН ЦЕН
#         "min_price": 99000,
#         "max_price": 100000
#     }
# }  # TODO ПРИМЕР файла JSON

with open("input.json", 'r', encoding="utf-8-sig") as file:  # открытие файла с вводимыми данными
    I_JSON = json.load(file)

# todo Блок парсинга вводимого JSON с первичной валидацией
# ПУНКТ НАЗНАЧЕНИЯ
destination = I_JSON["destination"].lower().strip()
# ДИАПАЗОН ВЫЛЕТА
start_date = datetime.datetime.strptime(I_JSON["departure_dates"]["start_date"], "%Y-%m-%d").date()
end_date = datetime.datetime.strptime(I_JSON["departure_dates"]["end_date"], "%Y-%m-%d").date()
# Проверка корректности ввода дат
today = datetime.datetime.now().date()
today_day = today.day
today_month = today.month
today_year = today.year

if start_date <= today or end_date <= today or start_date > end_date or (end_date - start_date).days > 20:
    raise ValueError("Не корректный ввод даты. (Возможно превышение 20 дней на диапазон вылета)")
# _______________________________

# ПРОДОЛЖИТЕЛЬНОСТЬ ТУРА
min_duration = I_JSON["duration"]["min_duration"]
max_duration = I_JSON["duration"]["max_duration"]
if min_duration < 1 or max_duration < 1 or min_duration > 28 or max_duration > 28 or (max_duration - min_duration) > 14:
    raise ValueError(
        "Не корректный ввод продолжительности тура. (Возможно превышение 28 дней или разница между минимумом и максимумом более 14.)")
# ПИТАНИЕ
board_type = I_JSON["board_type"].lower().strip()
# КОЛИЧЕСТВО ЗВЕЗД ОТЕЛЯ
min_hotel_stars = min([abs(I_JSON["hotel_stars"]["min_stars"]), abs(I_JSON["hotel_stars"]["max_stars"])])
max_hotel_stars = max([abs(I_JSON["hotel_stars"]["min_stars"]), abs(I_JSON["hotel_stars"]["max_stars"])])

if min_hotel_stars > 5 or max_hotel_stars > 5:
    raise ValueError("Не корректно введен минимальный или максимальное количество звёзд.")

# ЦЕНОВОЙ ДИАПАЗОН TODO узнать о валютах(???)
min_price = min([abs(I_JSON["price_range"]["min_price"]), abs(I_JSON["price_range"]["max_price"])])
max_price = max([abs(I_JSON["price_range"]["min_price"]), abs(I_JSON["price_range"]["max_price"])])
# ______________________________________________________________________________________________________________________

def set_filters(browser: Chrome):
    """
    Функция задающая фильтрацию поиска туров по заданным параметрам из JSON файла.

    :param browser: Chrome
    :return: None
    """
    browser.get("https://tourvisor.ru/search.php")
    wait = WebDriverWait(browser, 10, ignored_exceptions=[selenium.common.ElementClickInterceptedException,
                                                          selenium.common.NoSuchElementException,
                                                          selenium.common.TimeoutException])
    wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR,
                                    'div[class="TVHotelList TVStyleScroll TVMultiSelectionEnabled"]')))  # Ожидание загрузки контента на странице

    # todo ПУНКТ НАЗНАЧЕНИЯ ____________________________________________________________________________________________
    destination_button = \
        browser.find_element(By.CSS_SELECTOR, 'div[class="TVCountryFilter"]').find_elements(By.CSS_SELECTOR,
                                                                                            'div[class="TVMainSelectContent"]')[
            0]  # Поиск вкладки - ПУНКТ НАЗНАЧЕНИЯ
    destination_button.click()
    time.sleep(0.1)
    wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[class="TVCountrySelectTooltipHeader"]')))

    not_only_charter_flights = browser.find_element(By.CSS_SELECTOR,
                                                    'div[class="TVCountrySelectTooltipHeader"]').find_element(
        By.CSS_SELECTOR, 'div[class="TVCheckBox TVChecked"]')  # Поиск, включая рейсы С ПЕРЕСАДКАМИ
    not_only_charter_flights.click()

    # Поиск по ВСЕМ рейсам
    wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[class="TVCountryAirportListWithTabs"]')))
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[class="TVTabListItem"]')))

    country_buttons = browser.find_element(By.CSS_SELECTOR,
                                           'div[class="TVTabListControl TVStyleScroll TVStyleTheme2 TVPaddingSize-S TVFontSize-S TVScrollHidden"]').find_elements(
        By.CSS_SELECTOR, 'div[class][title]')
    for country_button in country_buttons:  # Цикл перебора кнопок(web-элементов) с целью найти кнопку "Все"(страны)
        if 'все' in country_button.text.lower():
            country_button.click()
    # _________________

    wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[class="TVComplexListItemContentWrapper"]')))

    # Выбор пункта назначения
    country_buttons = browser.find_elements(By.CSS_SELECTOR, 'div[class="TVComplexListItemContent"]')
    for country_button in country_buttons:  # Цикл перебора кнопок(web-элементов) с целью найти нужную страну и выбрать
        if country_button.text.lower().strip() == destination:
            country_button.click()
            break
    # _______________________

    # todo _____________________________________________________________________________________________________________

    # todo ДИАПАЗОН ВЫЛЕТА _____________________________________________________________________________________________
    time.sleep(0.1)
    fly_dates_button = browser.find_element(By.CSS_SELECTOR, 'div[class="TVFlyDatesFilter"]').find_element(
        By.CSS_SELECTOR, 'div[class="TVMainSelectContent"]')  # Поиск вкладки - ДАТА ВЫЛЕТА
    fly_dates_button.click()
    time.sleep(0.1)
    wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[class="TVCalendarSheetControlTitle"]')))

    # Поиск нужных месяцев календаря
    while utils.DATES[browser.find_elements(By.CSS_SELECTOR, 'div[class="TVCalendarTitleControlMonth"]')[
        0].text.strip().lower()] != datetime.datetime.strptime(
        I_JSON["departure_dates"]["start_date"], "%Y-%m-%d").date().month:
        browser.find_element(By.CSS_SELECTOR, 'div[class="TVCalendarSliderViewRightButton"]').click()
        wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[class="TVCalendarSliderViewRightButton"]')))
    # ______________________________
    left_calendar = browser.find_elements(By.CSS_SELECTOR, 'div[class="TVCalendarSheetControlBody"]')[0]
    right_calendar = browser.find_elements(By.CSS_SELECTOR, 'div[class="TVCalendarSheetControlBody"]')[-1]

    time.sleep(0.3)
    start_date_button = left_calendar.find_element(By.CSS_SELECTOR, f't-td[data-value="{start_date.day}"]')
    start_date_button.click()
    time.sleep(0.1)
    if start_date.month == end_date.month:
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f't-td[data-value="{end_date.day}"]')))
        end_date_button = left_calendar.find_element(By.CSS_SELECTOR, f't-td[data-value="{end_date.day}"]')
        end_date_button.click()
    else:
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f't-td[data-value="{end_date.day}"]')))
        end_date_button = right_calendar.find_element(By.CSS_SELECTOR, f't-td[data-value="{end_date.day}"]')
        end_date_button.click()
    # todo _____________________________________________________________________________________________________________

    # todo ПРОДОЛЖИТЕЛЬНОСТЬ ТУРА ______________________________________________________________________________________
    # wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[class=" TVRangeSelect"]')))
    time.sleep(1)
    duration_button = browser.find_element(By.CSS_SELECTOR, 'div[class*="TVRangeSelect"]').find_element(By.CSS_SELECTOR,
                                                                                                        'div[class="TVMainSelectContent"]')  # Поиск кнопки ПРОДОЛЖИТЕЛЬНОСТИ ТУРА(Ночи в отеле)
    duration_button.click()
    time.sleep(1)
    min_duration_button = \
        browser.find_element(By.CSS_SELECTOR, 'div[class="TVRangeTableContainer"]').find_elements(By.CSS_SELECTOR,
                                                                                                  'div[class*="TVRangeTableCell"]')[
            min_duration - 1]
    min_duration_button.click()
    time.sleep(1)
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[class="TVRangeTableContainer"]')))
    max_duration_button = \
        browser.find_element(By.CSS_SELECTOR, 'div[class="TVRangeTableContainer"]').find_elements(By.CSS_SELECTOR,
                                                                                                  'div[class*="TVRangeTableCell"]')[
            max_duration - 1]
    max_duration_button.click()
    time.sleep(0.3)
    # todo _____________________________________________________________________________________________________________

    # todo ПИТАНИЕ _____________________________________________________________________________________________________
    if board_type in list(utils.BOARD_TYPES):  # (???)
        board_type_button = browser.find_element(By.CSS_SELECTOR,
                                                 'div[class="TVMealFilter"]').find_element(By.CSS_SELECTOR,
                                                                                           'div[class="TVRadioGroupSelect"]')  # Поиск вкладки - ПИТАНИЕ
        board_type_button.click()
        time.sleep(0.1)
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[class="TVRadioGroupSelectTooltipContent"]')))

        board_type_input_radio = browser.find_element(By.CSS_SELECTOR,
                                                      'div[class="TVRadioGroupSelectTooltipContent"]').find_elements(
            By.CSS_SELECTOR, 'input[class="TVInputRadioInput"]')[utils.BOARD_TYPES[board_type]]
        board_type_input_radio.click()
        time.sleep(0.1)
    # todo _____________________________________________________________________________________________________________

    # todo РЕЙТИНГ ОТЕЛЯ _______________________________________________________________________________________________
    if min_hotel_stars >= 3:
        hotel_start_button = browser.find_element(By.CSS_SELECTOR,
                                                  'div[class="TVHotelRatingFilter"]').find_element(By.CSS_SELECTOR,
                                                                                                   'div[class="TVRadioGroupSelect"]')  # Поиск вкладки - РЕЙТИНГ ОТЕЛЯ
        hotel_start_button.click()
        time.sleep(0.2)
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[class="TVRadioGroupSelectTooltipContent"]')))

        if list(utils.MIN_HOTEL_STARS)[0][0] <= min_hotel_stars < list(utils.MIN_HOTEL_STARS)[0][-1]:
            min_hotel_stars_input_radio = browser.find_element(By.CSS_SELECTOR,
                                                               'div[class="TVRadioGroupSelectTooltipContent"]').find_elements(
                By.CSS_SELECTOR, 'input[class="TVInputRadioInput"]')[
                utils.MIN_HOTEL_STARS[list(utils.MIN_HOTEL_STARS)[0]]]
            min_hotel_stars_input_radio.click()


        elif list(utils.MIN_HOTEL_STARS)[1][0] <= min_hotel_stars < list(utils.MIN_HOTEL_STARS)[1][-1]:
            min_hotel_stars_input_radio = browser.find_element(By.CSS_SELECTOR,
                                                               'div[class="TVRadioGroupSelectTooltipContent"]').find_elements(
                By.CSS_SELECTOR, 'div[class="TVInputRadioLabel"]')[
                utils.MIN_HOTEL_STARS[list(utils.MIN_HOTEL_STARS)[1]]]
            min_hotel_stars_input_radio.click()

        elif list(utils.MIN_HOTEL_STARS)[2][0] <= min_hotel_stars < list(utils.MIN_HOTEL_STARS)[2][-1]:
            min_hotel_stars_input_radio = browser.find_element(By.CSS_SELECTOR,
                                                               'div[class="TVRadioGroupSelectTooltipContent"]').find_elements(
                By.CSS_SELECTOR, 'div[class="TVInputRadioLabel"]')[
                utils.MIN_HOTEL_STARS[list(utils.MIN_HOTEL_STARS)[2]]]
            min_hotel_stars_input_radio.click()

        elif list(utils.MIN_HOTEL_STARS)[3][0] <= min_hotel_stars < list(utils.MIN_HOTEL_STARS)[3][-1]:
            min_hotel_stars_input_radio = browser.find_element(By.CSS_SELECTOR,
                                                               'div[class="TVRadioGroupSelectTooltipContent"]').find_elements(
                By.CSS_SELECTOR, 'div[class="TVInputRadioLabel"]')[
                utils.MIN_HOTEL_STARS[list(utils.MIN_HOTEL_STARS)[3]]]
            min_hotel_stars_input_radio.click()
        # Можно переписать в цикл (тут перебираются диапазоны звёзд отеля для фильтрации на сайте)
        time.sleep(0.1)
    # todo _____________________________________________________________________________________________________________

    # todo ДИАПАЗОН ЦЕН ________________________________________________________________________________________________
    price_range_button = browser.find_element(By.CSS_SELECTOR, 'div[class="TVBudgetFilter"]').find_element(
        By.CSS_SELECTOR, 'div[class="TVAddSelectArrow')
    price_range_button.click()
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[class="TVBudgetSelectTooltipContent"]')))

    browser.find_element(By.CSS_SELECTOR, 'div[class="TVBudgetSelectTooltipContent"]').find_element(
        By.CSS_SELECTOR, 'input[class="TVTourBudgetInput TVTourBudgetMinPriceInput"]').send_keys(
        min_price)  # Установка минимума

    browser.find_element(By.CSS_SELECTOR, 'div[class="TVBudgetSelectTooltipContent"]').find_element(
        By.CSS_SELECTOR, 'input[class="TVTourBudgetInput TVTourBudgetMaxPriceInput"]').send_keys(
        max_price)  # Установка максимума

    currency_input_radio = \
        browser.find_element(By.CSS_SELECTOR, 'div[class="TVBudgetSelectTooltipContent"]').find_elements(
            By.CSS_SELECTOR, 'input[class="TVInputRadioInput"]')[0]  # установка валюты(руб)# todo валюта - рубли (???)
    currency_input_radio.click()
    # todo _____________________________________________________________________________________________________________

    # todo ПОИСК ТУРОВ _________________________________________________________________________________________________
    search_button = browser.find_element(By.CSS_SELECTOR, 'div[class="TVSearchButton TVButtonColor TVButtonHover"]')
    search_button.click()


def parse_target_elements_and_links(browser: Chrome):
    """
    Функция сбора данных по турам

    :param browser: webdriver
    :return: None | list[selenium.element]
    """
    wait = WebDriverWait(browser, 10, ignored_exceptions=[selenium.common.ElementClickInterceptedException,
                                                          selenium.common.NoSuchElementException,
                                                          selenium.common.exceptions.TimeoutException])
    while True:  # Ожидание загрузки вариантов туров по заданным фильтрам
        print("...")
        try:
            browser.find_element(By.CSS_SELECTOR, 'div[class="TVProgressLine TVActive"][style="width: 100%;"]')
            break
        except:
            time.sleep(0.2)
            continue

    count_tours = 0
    while True:  # Нажатие "Найти еще туры" до упора
        print("Click!")
        try:
            browser.find_element(By.CSS_SELECTOR, 'div[class="TVSRSearchMoreBtn TVButtonColor"]').click()
            time.sleep(0.5)
            if count_tours == 0:
                count_tours = len(
                    browser.find_elements(By.CSS_SELECTOR, 'div[class="blpricesort"] div[class="TVHotelResultItem"]'))
            elif count_tours < len(
                    browser.find_elements(By.CSS_SELECTOR, 'div[class="blpricesort"] div[class="TVHotelResultItem"]')):
                count_tours = len(
                    browser.find_elements(By.CSS_SELECTOR, 'div[class="blpricesort"] div[class="TVHotelResultItem"]'))
                continue
            else:
                break
        except:
            break
    time.sleep(0.2)

    page_source_soup = BeautifulSoup(browser.page_source, 'lxml')
    try:  # Проверка на наличие найденных туров по заданным фильтрам
        page_source_soup.find('div', {"class": "TVResultItemBodyWrapper"})
    except:
        print("!!! По заданным параметрам не найдено туров, попробуйте обновить вводимы параметры фильтрации !!!")
        return None

    all_tours = browser.find_elements(By.CSS_SELECTOR,
                                      'div[class="blpricesort"] div[class="TVHotelResultItem"]')  # Элементы всех предложенных туров
    target_tours = list(filter(None, [tour if min_hotel_stars <= float(
        tour.find_element(By.CSS_SELECTOR, 'div[class*="TVHotelInfoRating"]').text) <= max_hotel_stars else None for
                                      tour in
                                      all_tours]))  # Элементы предложений туров, подходящие по критерию рейтинга

    """ Может быть разница между all_tours и target_tours, так как верхняя граница не задается на фильтре сайте и ее следует отслеживать в карточке товара """
    print(f"Всего туров найдено - {len(all_tours)}.")
    print(f"Подходящих туров найдено - {len(target_tours)}.")
    target_tours = [target_tour_button.find_element(By.CSS_SELECTOR, 'a[href][target]') for target_tour_button in
                    target_tours]

    return target_tours
    # _____________________
    # todo _____________________________________________________________________________________________________________


def parse_data_from_tour_card(browser: Chrome, target_elements: list, actions: ActionChains):
    """
    Функция собирающая данные из карточек предложенных туров

    :param browser: Chrome driver
    :param target_elements: list[selenium.elements]
    :param target_links: list[str(tour link)]
    :return: dict with result
    """
    RESULT = dict()  # todo СЛОВАРЬ, КОТОРЫЙ БУДЕТ НАПОЛНЯТЬСЯ ДАННЫМИ

    wait = WebDriverWait(browser, 10, ignored_exceptions=[selenium.common.ElementClickInterceptedException,
                                                          selenium.common.NoSuchElementException,
                                                          selenium.common.TimeoutException,
                                                          selenium.common.exceptions.TimeoutException])

    for inx_target_element, hotel_target_element in enumerate(target_elements):  # Цикл прохода по найденным карточкам туров
        try:
            actions.move_to_element(hotel_target_element).click().perform()

            print(hotel_target_element.text.strip())

            time.sleep(1)

            browser.implicitly_wait(0.5)

            """ 
                Открываем карточки туров в цикле.
            """

            # проверка о загрузке информации о перелетах в течение 50 секунд в цикле с шагом 10 и time.sleep - 5
            status = False  # Флаг отражающий, есть ли в карточке тура информация о перелетах (по дефолту предполагаем, что нет)
            for i in range(5):  # Цикл попыток найти информацию о перелете
                try:
                    try:
                        # проверка карточки на наличие сообщения о том, что информацию о перелетах необходимо уточнять у менеджеров
                        text = browser.find_element(By.XPATH, "//div[@class='TVTourFlightMessage TVTourFlightUnknown']")
                        if text:
                            print('Информация о турах доступна только у менеджеров компании')
                            break
                    except:
                        pass
                    # проверка карточки об информации о перелетах
                    check_TVTourFlightControl = browser.find_element(By.XPATH, "//div[@class='TVTourFlightControl']")

                    if check_TVTourFlightControl:
                        print('===== Информация о перелетах подрузилась ======')
                        status = True  # Переводим флажок в статус True, т.е. найдена информация о перелете
                        break
                except:
                    print(f'==== Ждем появления информации о перелетах,  попытка ---> {i + 1} ====')
                    time.sleep(0.1)

            if not status:  # Если нет информации о перелете, то пропускаем тур
                try:
                    close_tour_button = browser.find_element(By.XPATH, '//div[@class="TVClosePopUp"]')
                    actions.move_to_element(close_tour_button).click().perform()
                    continue
                except:
                    try:
                        time.sleep(0.1)
                        close_tour_button = browser.find_element(By.CSS_SELECTOR, 'div[class="TVClosePopUp"]')
                        actions.move_to_element(close_tour_button).click().perform()
                        continue
                    except:
                        continue

            RESULT[inx_target_element] = {}  # todo Заводим словарь отеля

            # Блок сбора информации о туре
            browser.implicitly_wait(0.5)
            try:
                Название_отеля = browser.find_element(By.CSS_SELECTOR,
                                                      'div[class="TVHotelTitleName TVHotelTitleCapitalize"]').text.strip()
            except:
                Название_отеля = None

            try:
                Расположение_отеля = browser.find_element(By.CSS_SELECTOR,
                                                          'div[class="TVHotelTitleResort"]').text.strip()
            except:
                Расположение_отеля = None

            try:
                Заезд = browser.find_element(By.CSS_SELECTOR,
                                             'div[class="TVTourCardOption TVCalendarIcon"] div[class="TVTourCardOptionHeader"]').text.strip()
            except:
                Заезд = None

            try:
                Количество_ночей = int(browser.find_element(By.CSS_SELECTOR,
                                                            'div[class="TVTourCardOption TVCalendarIcon"] div[class="TVTourCardOptionFooter"]').text.strip().split()[
                                           0])
            except:
                Количество_ночей = None

            try:
                Питание = browser.find_element(By.CSS_SELECTOR,
                                               'div[class="TVTourCardOption TVMealIcon"] div[class="TVTourCardOptionFooter"]').text.strip()
            except:
                Питание = None

            try:
                Услуги = browser.find_element(By.CSS_SELECTOR,
                                              'div[class="TVTourCardOption TVGearIcon"] div[class="TVTourCardOptionFooter"]').text.strip()
            except:
                Услуги = None
            # ____________________________
            time.sleep(0.1)

            # todo Блок сбора информации об отеле
            try:
                wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'div[class="TVHotelTitleStar"]')))
            except:
                print(' ======= Блок сбора информации об отеле error ==========')
            try:
                Количество_звезд = len(browser.find_elements(By.CSS_SELECTOR, 'div[class="TVHotelTitleStar"]'))
            except:
                Количество_звезд = None

            try:
                Дата_постройки = browser.find_element(By.CSS_SELECTOR,
                                                      'div[class="TVHotelBuild TVDescriptionData TVHide"]').text.strip()
            except:
                Дата_постройки = None

            try:
                Дата_ремонта = browser.find_element(By.CSS_SELECTOR,
                                                    'div[class="TVHotelRepair TVDescriptionData TVHide"]').text.strip()
            except:
                Дата_ремонта = None

            try:
                Общая_информаци = browser.find_element(By.CSS_SELECTOR,
                                                       'div[class="TVHotelPlacement TVDescriptionData"]').text.strip()
            except:
                Общая_информаци = None

            try:
                Площадь = browser.find_element(By.CSS_SELECTOR,
                                               'div[class="TVHotelSquare TVDescriptionData TVHide"]').text.strip()
            except:
                Площадь = None

            try:
                Телефон = browser.find_element(By.CSS_SELECTOR,
                                               'div[class="TVHotelPhone TVDescriptionData TVHide"]').text.strip()
            except:
                Телефон = None

            try:
                Пляж = browser.find_element(By.CSS_SELECTOR,
                                            'div[class="TVDescriptionItem TVHotelBeach"]').text.strip()
            except:
                Пляж = None

            try:
                Территория_отеля = browser.find_element(By.CSS_SELECTOR,
                                                        'div[class="TVDescriptionItem TVHotelTerritory"]').text.strip()
            except:
                Территория_отеля = None

            try:
                Концепция_питания = browser.find_element(By.CSS_SELECTOR,
                                                         'div[class="TVDescriptionItem TVHotelMealTypes"]').text.strip()
            except:
                Концепция_питания = None

            try:
                В_номере = browser.find_element(By.CSS_SELECTOR,
                                                'div[class="TVDescriptionItem TVHotelInRoom"]').text.strip()
            except:
                В_номере = None

            try:
                Типы_номеров = browser.find_element(By.CSS_SELECTOR,
                                                    'div[class="TVDescriptionItem TVHotelRoomTypes"]').text.strip()
            except:
                Типы_номеров = None

            # ______________________________
            time.sleep(0.1)

            # todo Блок сбора отзывов об отеле
            try:
                Отзывы = []  # Список, в который будут собираться отзывы об отеле
                reviews_button = browser.find_element(By.CSS_SELECTOR,
                                                      'div[class="TVHotelReviewsBtn TVButtonHover"]')  # Поиск кнопки вкладки отзывов
                reviews_button.click()
                wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'div[class="TVReviewContent"]')))
                review_elements = browser.find_elements(By.CSS_SELECTOR, 'div[class="TVReviewContent"]')
                for review_element in review_elements:  # Цикл добавления отзывов в список
                    Отзывы.append(review_element.text.strip())
            except:
                Отзывы = None

            # ___________________________
            time.sleep(0.1)
            # todo Блок сбора геопозиции отеля
            try:
                geo_button = browser.find_element(By.CSS_SELECTOR,
                                                  'div[class="TVHotelMapBtn TVButtonHover"]')  # Поиск кнопки вкладки расположения на карте
                geo_button.click()
                browser.implicitly_wait(3)
                try:
                    google_maps = browser.find_element(By.CSS_SELECTOR,
                                                       'a[class="TVMapButton TVSRGoogleLink"]').get_attribute(
                        "href")
                except:
                    google_maps = None

                try:
                    yandex_maps = browser.find_element(By.CSS_SELECTOR,
                                                       'a[class="TVMapButton TVYandexLink"]').get_attribute("href")
                except:
                    yandex_maps = None
            except:
                google_maps = None
                yandex_maps = None
            # __________________________

            hotel = {}  # todo Словарь для хранения информации об отеле
            hotel["Название_отеля"] = Название_отеля
            hotel["Расположение_отеля"] = Расположение_отеля
            hotel["Заезд"] = Заезд
            hotel["Количество_ночей"] = Количество_ночей
            hotel["Питание"] = Питание
            hotel["Услуги"] = Услуги

            hotel["Количество_звезд"] = Количество_звезд
            hotel["Дата_постройки"] = Дата_постройки
            hotel["Дата_ремонта"] = Дата_ремонта
            hotel["Общая_информаци"] = Общая_информаци
            hotel["Площадь"] = Площадь
            hotel["Телефон"] = Телефон
            hotel["Пляж"] = Пляж
            hotel["Территория_отеля"] = Территория_отеля
            hotel["Концепция_питания"] = Концепция_питания
            hotel["В_номере"] = В_номере
            hotel["Типы_номеров"] = Типы_номеров
            hotel["Отзывы"] = Отзывы
            hotel["google_maps"] = google_maps
            hotel["yandex_maps"] = yandex_maps

            RESULT[inx_target_element]["Отель"] = hotel.copy()  # Добавление в текущий тур информации об отеле

            # проверяем, есть ли информация о других рейсах
            browser.implicitly_wait(0.5)
            count_flights = 1
            for i in range(5):
                try:
                    change_flight_button = browser.find_element(By.CSS_SELECTOR, 'div[class="TVTourFlightMoreButton"]')
                    actions.move_to_element(change_flight_button).click().perform()
                    time.sleep(0.3)
                    count_flights = len(
                        browser.find_elements(By.CSS_SELECTOR, 'div[class*="TVFlightSelectionButton "]'))
                    break
                except:
                    print(f'==== Ждем появления кнопки информации о других перелетах, попытка ---> {i + 1} ====')
                    time.sleep(0.5)

            RESULT[inx_target_element]["Перелеты"] = []  # todo Список для хранения информации о вариантах перелетов(и их итоговые цены)
            for num_flight in range(count_flights):  # Цикл прохода по возможным перелетам
                if count_flights != 1:
                    flight_button = browser.find_elements(By.CSS_SELECTOR,
                                                          'div[class="TVFlightSelectionBlock"] div[class*="TVFlightSelectionButton "]')
                    actions.move_to_element(flight_button[num_flight]).click().perform()

                try:
                    Цена = round(float(
                        browser.find_element(By.CSS_SELECTOR, 'div[class="TVTourCardPriceValue"]').text.strip().replace(
                            ' ', '')), 2)

                except:
                    Цена = None

                try:
                    # todo Блок сбора информации о перелетах

                    wait.until(EC.visibility_of_element_located(
                        (By.XPATH, "//div[@class='TVTourFlightControl']")))  # div[class="TVTourFlightControl"]
                    flights_info_buttons = browser.find_elements(By.CSS_SELECTOR, 'div[class="TVTourFlightInfo"]')
                    for inx, flights_info_button in enumerate(flights_info_buttons):  # Цикл прохода по кнопкам найденных возможных перелетов
                        flights_info_button.click()
                        actions.move_to_element(
                            browser.find_element(By.CSS_SELECTOR, 'div[class="TVFlightDetailControl"]'))
                        if inx == 0:
                            time.sleep(1.1)
                            try:
                                Номер_рейса_туда = browser.find_element(By.CSS_SELECTOR,
                                                                        'div[class="TVFlightDetailControl"] div[class="TVFlightDetailNumber"]').text.strip()
                            except:
                                Номер_рейса_туда = None
                            try:
                                Компания_туда = browser.find_element(By.CSS_SELECTOR,
                                                                     'div[class="TVFlightDetailControl"] div[class="TVFlightDetailAirlineName"]').text.strip()
                            except:
                                Компания_туда = None
                            try:
                                Тип_рейса_туда = browser.find_element(By.CSS_SELECTOR,
                                                                      'div[class="TVFlightDetailControl"] div[class="TVFlightDetailType"]').text.strip()
                            except:
                                Тип_рейса_туда = None
                            try:
                                Багаж_туда = browser.find_element(By.CSS_SELECTOR,
                                                                  'div[class="TVFlightDetailControl"] div[class="TVFlightDetailBaggage"]').text.strip()
                            except:
                                Багаж_туда = None

                            try:
                                День_вылета_туда = browser.find_element(By.CSS_SELECTOR,
                                                                        'div[class="TVFlightDetailControl"] div[class="TVFlightDetailDepartureDate"]').text.strip()
                            except:
                                День_вылета_туда = None
                            try:
                                Время_вылет_туда = browser.find_element(By.CSS_SELECTOR,
                                                                        'div[class="TVFlightDetailControl"] div[class="TVFlightDetailDepartureTime"]').text.strip()
                            except:
                                Время_вылет_туда = None
                            try:
                                Аэропорт_вылета_туда = browser.find_elements(By.CSS_SELECTOR,
                                                                             'div[class="TVFlightDetailControl"] div[class="TVFlightDetailPortId"]')[
                                    0].text.strip()
                            except:
                                Аэропорт_вылета_туда = None

                            try:
                                Время_полета_туда = browser.find_element(By.CSS_SELECTOR,
                                                                         'div[class="TVFlightDetailControl"] div[class="TVFlightDetailDuration"]').text.strip()
                            except:
                                Время_полета_туда = None

                            try:
                                День_посадки_туда = browser.find_element(By.CSS_SELECTOR,
                                                                         'div[class="TVFlightDetailControl"] div[class="TVFlightDetailArrivalDate"]').text.strip()
                            except:
                                День_посадки_туда = None
                            try:
                                Время_посадки_туда = browser.find_element(By.CSS_SELECTOR,
                                                                          'div[class="TVFlightDetailControl"] div[class="TVFlightDetailArrivalTime"]').text.strip()
                            except:
                                Время_посадки_туда = None
                            try:
                                Аэропорт_посадки_туда = browser.find_elements(By.CSS_SELECTOR,
                                                                              'div[class="TVFlightDetailControl"] div[class="TVFlightDetailPortId"]')[
                                    1].text.strip()
                            except:
                                Аэропорт_посадки_туда = None

                            try:
                                close_forward_button = browser.find_element(By.CSS_SELECTOR,
                                                                            'div[class="tv_content"] div[class="TVClosePopUp"]')  # Кнопка закрытия вкладки информации о полете
                                actions.move_to_element(close_forward_button).click().perform()
                            except:
                                pass

                        else:
                            time.sleep(1.1)

                            try:
                                Номер_рейса_обратно = browser.find_element(By.CSS_SELECTOR,
                                                                           'div[class="TVFlightDetailControl"] div[class="TVFlightDetailNumber"]').text.strip()
                            except:
                                Номер_рейса_обратно = None
                            try:
                                Компания_обратно = browser.find_element(By.CSS_SELECTOR,
                                                                        'div[class="TVFlightDetailControl"] div[class="TVFlightDetailAirlineName"]').text.strip()
                            except:
                                Компания_обратно = None
                            try:
                                Тип_рейса_обратно = browser.find_element(By.CSS_SELECTOR,
                                                                         'div[class="TVFlightDetailControl"] div[class="TVFlightDetailType"]').text.strip()
                            except:
                                Тип_рейса_обратно = None
                            try:
                                Багаж_обратно = browser.find_element(By.CSS_SELECTOR,
                                                                     'div[class="TVFlightDetailControl"] div[class="TVFlightDetailBaggage"]').text.strip()
                            except:
                                Багаж_обратно = None

                            try:
                                День_вылета_обратно = browser.find_element(By.CSS_SELECTOR,
                                                                           'div[class="TVFlightDetailControl"] div[class="TVFlightDetailDepartureDate"]').text.strip()
                            except:
                                День_вылета_обратно = None
                            try:
                                Время_вылет_обратно = browser.find_element(By.CSS_SELECTOR,
                                                                           'div[class="TVFlightDetailControl"] div[class="TVFlightDetailDepartureTime"]').text.strip()
                            except:
                                Время_вылет_обратно = None
                            try:
                                Аэропорт_вылета_обратно = browser.find_elements(By.CSS_SELECTOR,
                                                                                'div[class="TVFlightDetailControl"] div[class="TVFlightDetailPortId"]')[
                                    0].text.strip()
                            except:
                                Аэропорт_вылета_обратно = None

                            try:
                                Время_полета_обратно = browser.find_element(By.CSS_SELECTOR,
                                                                            'div[class="TVFlightDetailControl"] div[class="TVFlightDetailDuration"]').text.strip()
                            except:
                                Время_полета_обратно = None

                            try:
                                День_посадки_обратно = browser.find_element(By.CSS_SELECTOR,
                                                                            'div[class="TVFlightDetailControl"] div[class="TVFlightDetailArrivalDate"]').text.strip()
                            except:
                                День_посадки_обратно = None
                            try:
                                Время_посадки_обратно = browser.find_element(By.CSS_SELECTOR,
                                                                             'div[class="TVFlightDetailControl"] div[class="TVFlightDetailArrivalTime"]').text.strip()
                            except:
                                Время_посадки_обратно = None
                            try:
                                Аэропорт_посадки_обратно = browser.find_elements(By.CSS_SELECTOR,
                                                                                 'div[class="TVFlightDetailControl"] div[class="TVFlightDetailPortId"]')[
                                    1].text.strip()
                            except:
                                Аэропорт_посадки_обратно = None

                            try:
                                close_reverse_button = browser.find_element(By.CSS_SELECTOR,
                                                                            'div[class="tv_content"] div[class="TVClosePopUp"]')  # Кнопка закрытия вкладки информации о полете
                                actions.move_to_element(close_reverse_button).click().perform()
                            except:
                                pass
                except:
                    print(
                        ' =========== Нет информации о перелетах (Сайт их не показывает либо для доступа необходимо связаться с менеджером)==============\n')
                    Номер_рейса_туда = None
                    Компания_туда = None
                    Тип_рейса_туда = None
                    Багаж_туда = None
                    День_вылета_туда = None
                    Время_вылет_туда = None
                    Аэропорт_вылета_туда = None
                    Время_полета_туда = None
                    День_посадки_туда = None
                    Время_посадки_туда = None
                    Аэропорт_посадки_туда = None
                    Номер_рейса_обратно = None
                    Компания_обратно = None
                    Тип_рейса_обратно = None
                    Багаж_обратно = None
                    День_вылета_обратно = None
                    Время_вылет_обратно = None
                    Аэропорт_вылета_обратно = None
                    Время_полета_обратно = None
                    День_посадки_обратно = None
                    Время_посадки_обратно = None
                    Аэропорт_посадки_обратно = None

                flight = {}  # todo Словарь для хранения

                flight["Цена"] = Цена
                flight["Номер_рейса_туда"] = Номер_рейса_туда
                flight["Компания_туда"] = Компания_туда
                flight["Тип_рейса_туда"] = Тип_рейса_туда
                flight["Багаж_туда"] = Багаж_туда
                flight["День_вылета_туда"] = День_вылета_туда
                flight["Время_вылет_туда"] = Время_вылет_туда
                flight["Аэропорт_вылета_туда"] = Аэропорт_вылета_туда
                flight["Время_полета_туда"] = Время_полета_туда
                flight["День_посадки_туда"] = День_посадки_туда
                flight["Время_посадки_туда"] = Время_посадки_туда
                flight["Аэропорт_посадки_туда"] = Аэропорт_посадки_туда
                flight["Номер_рейса_обратно"] = Номер_рейса_обратно
                flight["Компания_обратно"] = Компания_обратно
                flight["Тип_рейса_обратно"] = Тип_рейса_обратно
                flight["Багаж_обратно"] = Багаж_обратно
                flight["День_вылета_обратно"] = День_вылета_обратно
                flight["Время_вылет_обратно"] = Время_вылет_обратно
                flight["Аэропорт_вылета_обратно"] = Аэропорт_вылета_обратно
                flight["Время_полета_обратно"] = Время_полета_обратно
                flight["День_посадки_обратно"] = День_посадки_обратно
                flight["Время_посадки_обратно"] = Время_посадки_обратно
                flight["Аэропорт_посадки_обратно"] = Аэропорт_посадки_обратно

                RESULT[inx_target_element]["Перелеты"].append(flight.copy())
                browser.implicitly_wait(5)
                if count_flights > 1:
                    change_flight_button = browser.find_element(By.CSS_SELECTOR, 'div[class="TVTourFlightMoreButton"]')
                    actions.move_to_element(change_flight_button).click().perform()

                time.sleep(0.3)
                print(RESULT)
            close_tour_button = browser.find_element(By.XPATH, '//div[@class="TVClosePopUp"]')  # Поиск кнопки закрытия карточки тура
            actions.move_to_element(close_tour_button).click().perform()
            time.sleep(0.5)
        except Exception as ex:
            print(f"!!! СБОР ДАННЫХ ЗАВЕРШЕН С ОШИБКОЙ - ({ex})!!!")
            return RESULT

    return RESULT


if __name__ == '__main__':
    options = ChromeOptions()

    # в utils.py, в переменную PATH_TO_PROFILE нужно прописать путь до профиля в Гугл и в переменную PROFILE_NAME прописать наименование профиля
    """
    Пример:
        chromeOptions.add_argument('--user-data-dir=/Users/miroslav/Library/Application Support/Google/Chrome')
        chromeOptions.add_argument('--profile-directory=Profile 1')
    """
    options.add_argument(rf'--user-data-dir={utils.PATH_TO_PROFILE}')  # todo Настройка браузера на работу через определенного пользователя(с определенными настройками)...
    options.add_argument(f'--profile-directory={utils.PROFILE_NAME}')  # todo ... продолжение
    options.add_argument('--start-maximized')  # todo Работа с максимальным расширением браузера

    count_restart = 0
    while count_restart < 3:
        try:
            with uc.Chrome(options=options) as browser:  # todo Блок инициализации браузера
                browser.maximize_window()

                actions = ActionChains(browser)

                set_filters(browser=browser)  # Исполнение функции настройки фильтра сайта

                target_elements = parse_target_elements_and_links(browser=browser)  # Исполнение функции поиска web-элементов целевых туров

                RESULT = parse_data_from_tour_card(browser=browser, target_elements=target_elements, actions=actions)  #

                with open("RESULT.json", "w", encoding="utf-8-sig") as file:  # todo Блок сохранения результирующего словаря в JSON файл
                    json.dump(RESULT, file, ensure_ascii=False)
                print('!!! FINISH !!!')
        except OSError :
            count_restart += 1
            print(f"!!! Что-то пошло не так при запуске драйвера (Попытка №{count_restart}). Попробую еще раз ... !!!")
            time.sleep(3)
            continue
