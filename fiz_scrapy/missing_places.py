from fiz_scrapy.missing_place import MissingPlaceService


def import_missing_places(limit, place_id, mode, place, category_choice, sub_category_choice,
                          total_category, total_subcategory,
                          place_choice_name, cat_name, sub_cat_name, category_list):
    """
    :param limit:
    :param place_id:
    :param mode:
    :param place:
    :param category_choice:
    :param sub_category_choice:
    :param total_category:
    :param total_subcategory:
    :return:
    """

    service = MissingPlaceService()
    print "modeeeeeeeeeem", mode, "limitttttttttt", limit, "place_idddddd", place_id, \
        "cat choice", category_choice, "sub cat choice", sub_category_choice, \
        "total_categoryyy", total_category, "total_subcategoryyy", total_subcategory
    try:
        if mode == 1:
            place_list = []
            if int(limit) == 0:
                for category in category_list:
                    # if category.values()[2] != "0":
                    temp_list = service.tripadvisor_all(place_id, int(total_category), category['key'], "0", None)
                    place_list.append(temp_list)

                # things_to_do = service.tripadvisor_total_thingstodo(place_id)
                # place_list = service.tripadvisor_all(place_id, int(things_to_do), category_choice, "0", None)
            else:
                for category in category_list:
                    # if category.values()[2] != "0":
                    temp_list = service.tripadvisor_all(place_id, None, category['key'], "0", int(limit))
                    place_list.append(temp_list)

                # place_list = service.tripadvisor_all(place_id, None, category_choice, "0", int(limit))

            place_list = [val for sublist in place_list for val in sublist]

        elif mode == 2:
            if int(limit) == 0:
                place_list = service.tripadvisor_all(place_id, int(total_category), category_choice, sub_category_choice, None)
            else:
                place_list = service.tripadvisor_all(place_id, None, category_choice, sub_category_choice, int(limit))
        else:
            if int(limit) == 0:
                place_list = service.tripadvisor_all(place_id, int(total_subcategory), category_choice, sub_category_choice, None)
            else:
                place_list = service.tripadvisor_all(place_id, None, category_choice, sub_category_choice, int(limit))

        count = 1
        scraped_data_list = []
        for i in place_list:
            if limit != 0:
                if count <= limit:
                    scraped_data_list = service.third_party(i, scraped_data_list, place)
                    count += 1
                else:
                    break
            else:
                scraped_data_list = service.third_party(i, scraped_data_list, place)

        print scraped_data_list, 'temp_data####'

        return scraped_data_list

    except Exception as e:
        raise e
