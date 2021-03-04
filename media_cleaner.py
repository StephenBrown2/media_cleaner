#!/usr/bin/env python3

import hashlib
import json
import os
import sys
import traceback
import urllib
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib import request

from dateutil.parser import parse

# Hash password if not hashed
# if cfg.admin_password_sha1 == '':
#     cfg.admin_password_sha1=hashlib.sha1(cfg.admin_password.encode()).hexdigest()
# auth_key=''
# print('Hash:'+ cfg.admin_password_sha1)


def retjprint(rawjson):
    # return a formatted string of the python JSON object
    ezjson = json.dumps(rawjson, sort_keys=False, indent=4)
    return ezjson


def jprint(rawjson):
    # create a formatted string of the python JSON object
    ezjson = retjprint(rawjson)
    print(ezjson)


def get_brand():
    defaultbrand = "emby"
    print("0:emby\n1:jellyfin")
    brand = input("Enter number for server branding (default " + defaultbrand + "): ")
    if brand == "":
        return defaultbrand
    elif brand == "0":
        return defaultbrand
    elif brand == "1":
        return "jellyfin"
    else:
        print("Invalid choice. Default to emby.")
        return defaultbrand


def get_url():
    defaulturl = "http://localhost"
    url = input("Enter server ip or name (default " + defaulturl + "): ")
    if url == "":
        return defaulturl
    else:
        if url.find("://", 3, 7) >= 0:
            return url
        else:
            # print('No http:// or https:// entered.')
            url = "http://" + url
            print("Assuming server ip or name is: " + url)
            return url


def get_port():
    defaultport = "8096"
    print("If you have not explicity changed this option, press enter for default.")
    print("Space for no port.")
    port = input("Enter port (default " + defaultport + "): ")
    if port == "":
        return defaultport
    elif port == " ":
        return ""
    else:
        return port


def get_base(brand):
    defaultbase = "emby"
    # print('If you are using emby press enter for default.')
    if brand == defaultbase:
        print('Using "/' + defaultbase + '" as base url')
        return defaultbase
    else:
        print(
            "If you have not explicity changed this option in jellyfin, press enter for default."
        )
        print("For example: http://example.com/<baseurl>")
        base = input("Enter base url (default /" + defaultbase + "): ")
        if base == "":
            return defaultbase
        else:
            if base.find("/", 0, 1) == 0:
                return base[1 : len(base)]
            else:
                return base


def get_admin_username():
    return input("Enter admin username: ")


def get_admin_password():
    print(
        "Plain text password used to grab access token; hashed password stored in config file."
    )
    return input("Enter admin password: ")


def get_admin_password_sha1(password):
    # password_sha1=password #input('Enter admin password (password will be hashed in config file): ')
    return hashlib.sha1(password.encode()).hexdigest()


def generate_config():
    print("-----------------------------------------------------------")
    server_brand = get_brand()
    print("-----------------------------------------------------------")
    server = get_url()
    print("-----------------------------------------------------------")
    port = get_port()
    print("-----------------------------------------------------------")
    server_base = get_base(server_brand)
    if len(port):
        server_url = server + ":" + port + "/" + server_base
    else:
        server_url = server + "/" + server_base
    print("-----------------------------------------------------------")

    username = get_admin_username()
    print("-----------------------------------------------------------")
    password = get_admin_password()
    password_sha1 = get_admin_password_sha1(password)
    print("-----------------------------------------------------------")

    auth_key = get_auth_key(server_url, username, password, password_sha1)
    user_key = list_users(server_url, auth_key)
    print("-----------------------------------------------------------")

    not_played_age_movie = "100"
    not_played_age_episode = "100"
    not_played_age_video = "100"
    not_played_age_trailer = "100"

    config_file = ""
    config_file += "server_brand='" + server_brand + "'\n"
    config_file += "server_url='" + server_url + "'\n"
    config_file += "admin_username='" + username + "'\n"
    config_file += "admin_password_sha1='" + password_sha1 + "'\n"
    config_file += "access_token='" + auth_key + "'\n"
    config_file += "user_key='" + user_key + "'\n"
    config_file += "DEBUG=0\n"
    # config_file += "#----------------------------------------------------------#\n"
    # config_file += "#-1=Disable deleting for media type (movie, episode, video, trailer)#\n"
    # config_file += "# 0-365000=Delete media type once it has been watched x days ago#\n"
    # config_file += "#100=default#\n"
    config_file += "not_played_age_movie=" + not_played_age_movie + "\n"
    config_file += "not_played_age_episode=" + not_played_age_episode + "\n"
    config_file += "not_played_age_video=" + not_played_age_video + "\n"
    config_file += "not_played_age_trailer=" + not_played_age_trailer + "\n"
    # config_file += "not_played_age_audio="+ not_played_age_audio +"\n"
    # config_file += "not_played_age_season_folder="+ not_played_age_season_folder +"\n"
    # config_file += "not_played_age_tvchannel="+ not_played_age_tvchannel +"\n"
    # config_file += "not_played_age_program="+ not_played_age_program +"\n"
    # config_file += "#----------------------------------------------------------#\n"
    # config_file += "#----------------------------------------------------------#\n"
    # config_file += "#0=Disable deleting ALL media types#\n"
    # config_file += "#1=Enable deleteing ALL media types once past 'not_played_age_*' days ago#\n"
    # config_file += "#0=default#\n"
    config_file += "remove_files=0\n"
    # config_file += "#----------------------------------------------------------#\n"
    # config_file += "#----------------------------------------------------------#\n"
    # config_file += "#0=Ok to delete favorite of media type once past not_played_age_* days ago#\n"
    # config_file += "#1=Do no delete favorite of media type#\n"
    # config_file += "#(1=default)#\n"
    # config_file += "#Favoriting a series or season will treat all child episodes as if they are favorites#\n"
    config_file += "keep_favorites_movie=1\n"
    config_file += "keep_favorites_episode=1\n"
    config_file += "keep_favorites_video=1\n"
    config_file += "keep_favorites_trailer=1"
    # config_file += "keep_favorites_audio=1"
    # config_file += "keep_favorites_season_folder=1"
    # config_file += "keep_favorites_tvchannel=1"
    # config_file += "keep_favorites_program=1"
    # config_file += "\n#----------------------------------------------------------#"

    # Create config file next to the script even when cwd is not the same
    script_dir = Path(__file__).parent
    f = script_dir / "media_cleaner_config.py"
    f.write_text(config_file)

    print("\n\n-----------------------------------------------------------")
    print("Config file is not setup to delete media")
    print("To delete media set remove_files=1 in media_cleaner_config.py")
    print("-----------------------------------------------------------")
    print("Config file contents:")
    print("-----------------------------------------------------------")
    print(config_file)
    print("-----------------------------------------------------------")
    print("Config file created, try running again")
    print("-----------------------------------------------------------")


# Delete items
def delete_item(itemID):
    client = httpx.Client(base_url=cfg.server_url)
    url = f"/Items/{itemID}"
    params = {"api_key": cfg.access_token}
    if bool(cfg.DEBUG):
        # DEBUG
        print(itemID)
        print(cfg.server_url + url)
        print(params)
    if bool(cfg.remove_files):
        try:
            client.delete(url, params=params)
        except Exception:
            print("generic exception: " + traceback.format_exc())
    else:
        return


def get_auth_key(server_url, username, password, password_sha1):
    # Get Auth Token for admin account
    client = httpx.Client(base_url=server_url)

    values = {"Username": username, "Password": password_sha1, "Pw": password}

    emby_auth_dict = {
        "UserId": username,
        "Client": "media_cleaner",
        "Device": "media_cleaner",
        "DeviceId": "media_cleaner",
        "Version": "0.2",
    }
    emby_auth = ", ".join([f'{k}="{v}"' for k, v in emby_auth_dict.items()])
    headers = {"X-Emby-Authorization": f"Emby {emby_auth}"}

    req = client.post("/Users/AuthenticateByName", json=values, headers=headers)

    if req.status_code != 200:
        print("An error occurred while attempting to retrieve data from the API.")
        return ""

    return req.json()["AccessToken"]


def list_users(server_url, auth_key):
    # Get all users
    client = httpx.Client(base_url=server_url)
    url = "/Users"
    params = {"api_key": auth_key}
    req = client.get(url, params=params)

    if req.status_code != 200:
        print("An error occurred while attempting to retrieve data from the API.")
        return ""

    data = req.json()

    valid_user = False
    while not valid_user:
        for i, user in enumerate(data):
            print(f"{i}: {user['Name']} - {user['Id']}")

        user_number = input("Enter number for user to track: ")
        if (
            user_number.isdigit()
            and int(user_number) >= 0
            and int(user_number) < len(data)
        ):
            user_number = int(user_number)
            valid_user = True
        else:
            print("\nInvalid number. Try again.\n")

    userID = data[user_number]["Id"]
    return userID


def get_days_since_watched(date_last_played):
    # Get current time
    date_time_now = datetime.utcnow()

    # Keep the year, month, day, hour, minute, and seconds
    # split date_last_played after seconds
    try:
        split_date_micro_tz = date_last_played.split(".")
        date_time_last_watched = datetime.strptime(
            date_last_played, "%Y-%m-%dT%H:%M:%S." + split_date_micro_tz[1]
        )
    except (ValueError):
        date_time_last_watched = "unknown date time format"

    if bool(cfg.DEBUG):
        # DEBUG
        print(date_time_last_watched)

    if not (date_time_last_watched == "unknown date time format"):
        date_time_delta = date_time_now - date_time_last_watched
        s_date_time_delta = str(date_time_delta)
        days_since_watched = s_date_time_delta.split(" day")[0]
        if ":" in days_since_watched:
            days_since_watched = "Watched <1 day ago"
        elif days_since_watched == "1":
            days_since_watched = "Watched " + days_since_watched + " day ago"
        else:
            days_since_watched = "Watched " + days_since_watched + " days ago"
    else:
        days_since_watched = "0"
    return days_since_watched


def get_season_episode(season_number, episode_number):
    return f"s{season_number:02d}.e{episode_number:02d}"


def get_isfav_season_series(server_url, user_key, itemId, auth_key):
    # Get if season or series is marked as favorite for this item
    client = httpx.Client(base_url=server_url)
    url = f"/Users/{user_key}/Items/{itemId}"
    params = {"api_key": auth_key}

    if bool(cfg.DEBUG):
        # DEBUG
        print(url)

    req = client.get(url, params=params)
    if req.status_code != 200:
        print("An error occurred while attempting to retrieve data from the API.")
        return ""

    isfav_data = req.json()
    if bool(cfg.DEBUG):
        # print debug data to file
        with (Path(__file__).parent / "media_cleaner.debug").open(mode="a") as f:
            f.write(retjprint(isfav_data))

    return isfav_data["UserData"]["IsFavorite"]


def get_isfav(isfav, item, server_url, user_key, auth_key):
    # Check if episode's favorite value already exists in dictionary
    if not item["Id"] in isfav["episode"]:
        # Determine if this episode is marked as a favorite
        isfav["episode"][item["Id"]] = item["UserData"]["IsFavorite"]
    # Check if season's favorite value already exists in dictionary
    if not item["SeasonId"] in isfav["season"]:
        # Determine if the season is marked as a favorite
        isfav["season"][item["SeasonId"]] = get_isfav_season_series(
            server_url, user_key, item["SeasonId"], auth_key
        )
    # Check if series' favorite value already exists in dictionary
    if not item["SeriesId"] in isfav["series"]:
        # Determine if the series is marked as a favorite
        isfav["series"][item["SeriesId"]] = get_isfav_season_series(
            server_url, user_key, item["SeriesId"], auth_key
        )
    if bool(cfg.DEBUG):
        # DEBUG
        print("Episode is favorite: " + str(isfav["episode"][item["Id"]]))
        print(" Season is favorite: " + str(isfav["season"][item["SeasonId"]]))
        print(" Series is favorite: " + str(isfav["series"][item["SeriesId"]]))

    # Check if episode, season, or series is a favorite
    if (
        (isfav["episode"][item["Id"]])
        or (isfav["season"][item["SeasonId"]])
        or (isfav["series"][item["SeriesId"]])  # or
    ):
        # Either the episode, season, or series is set as a favorite
        itemIsFav = True
    else:
        # Neither the episode, season, or series is set as a favorite
        itemIsFav = False

    return itemIsFav


def get_items(server_url, user_key, auth_key):
    # Get list of all played items
    print("-----------------------------------------------------------")
    print("Start...")
    print("Cleaning media for server at: " + server_url)
    print("-----------------------------------------------------------")
    print("\n")
    print("-----------------------------------------------------------")
    print("Get List Of Watched Media")
    print("-----------------------------------------------------------")

    client = httpx.Client(base_url=server_url)
    url = f"/Users/{user_key}/Items"
    params = {
        "Recursive": "true",
        "IsPlayed": "true",
        "SortBy": "Type,SeriesName,ParentIndexNumber,IndexNumber,Name",
        "SortOrder": "Ascending",
        "api_key": auth_key,
    }
    req = client.get(url, params=params)

    if bool(cfg.DEBUG):
        # DEBUG
        print(url)

    if req.status_code != 200:
        print("An error occurred while attempting to retrieve data from the API.")
        return ""

    data = req.json()

    if bool(cfg.DEBUG):
        # print debug data to file
        with (Path(__file__).parent / "media_cleaner.debug").open(mode="a") as f:
            f.write(retjprint(data))

    # Go through all items and get ones not played in X days
    date_time_now = datetime.now(timezone.utc)
    cut_off_date_movie = date_time_now - timedelta(days=cfg.not_played_age_movie)
    cut_off_date_episode = date_time_now - timedelta(days=cfg.not_played_age_episode)
    cut_off_date_video = date_time_now - timedelta(days=cfg.not_played_age_video)
    cut_off_date_trailer = date_time_now - timedelta(days=cfg.not_played_age_trailer)
    deleteItems = []
    isfav = {"episode": {}, "season": {}, "series": {}}

    # Determine if media item is to be deleted or kept
    for item in data["Items"]:

        if item["Type"] == "Movie":
            if (
                (cfg.not_played_age_movie >= 0)
                and (item["UserData"]["PlayCount"] >= 1)
                and (cut_off_date_movie > parse(item["UserData"]["LastPlayedDate"]))
                and (
                    not bool(cfg.keep_favorites_movie)
                    or not item["UserData"]["IsFavorite"]
                )
            ):
                try:
                    item_details = "  " + " - ".join(
                        [
                            item["Type"],
                            item["Name"],
                            get_days_since_watched(item["UserData"]["LastPlayedDate"]),
                            "Favorite: " + item["UserData"]["IsFavorite"],
                            "MovieID: " + item["Id"],
                        ]
                    )
                    item_details = (
                        "  "
                        + item["Type"]
                        + " - "
                        + item["Name"]
                        + " - "
                        + get_days_since_watched(item["UserData"]["LastPlayedDate"])
                        + " - Favorite: "
                        + str(item["UserData"]["IsFavorite"])
                        + " - "
                        + "MovieID: "
                        + item["Id"]
                    )
                except (KeyError):
                    item_details = "  {Type} - {Name} - {Id}".format(**item)
                    if bool(cfg.DEBUG):
                        # DEBUG
                        print("\nError encountered - Delete Movie: \n" + str(item))
                print(":*[DELETE] - " + item_details)
                deleteItems.append(item)
            else:
                try:
                    item_details = (
                        "  "
                        + item["Type"]
                        + " - "
                        + item["Name"]
                        + " - "
                        + get_days_since_watched(item["UserData"]["LastPlayedDate"])
                        + " - Favorite: "
                        + str(item["UserData"]["IsFavorite"])
                        + " - "
                        + "MovieID: "
                        + item["Id"]
                    )
                except (KeyError):
                    item_details = "  {Type} - {Name} - {Id}".format(**item)
                    if bool(cfg.DEBUG):
                        # DEBUG
                        print("\nError encountered - Keep Movie: \n" + str(item))
                print(":[KEEPING] - " + item_details)
        elif item["Type"] == "Episode":
            # Get if episode, season, or series is set as favorite
            itemIsFav = get_isfav(isfav, item, server_url, user_key, auth_key)
            if (
                (cfg.not_played_age_episode >= 0)
                and (item["UserData"]["PlayCount"] >= 1)
                and (cut_off_date_episode > parse(item["UserData"]["LastPlayedDate"]))
                and (not bool(cfg.keep_favorites_episode) or (not itemIsFav))
            ):
                try:
                    item_details = (
                        item["Type"]
                        + " - "
                        + item["SeriesName"]
                        + " - "
                        + get_season_episode(
                            item["ParentIndexNumber"], item["IndexNumber"]
                        )
                        + " - "
                        + item["Name"]
                        + " - "
                        + get_days_since_watched(item["UserData"]["LastPlayedDate"])
                        + " - Favorite: "
                        + str(itemIsFav)
                        + " - "
                        + "EpisodeID: "
                        + item["Id"]
                    )
                except (KeyError):
                    item_details = "  {Type} - {Name} - {Id}".format(**item)
                    if bool(cfg.DEBUG):
                        # DEBUG
                        print("\nError encountered - Delete Episode: \n" + str(item))
                print(":*[DELETE] - " + item_details)
                deleteItems.append(item)
            else:
                try:
                    item_details = (
                        item["Type"]
                        + " - "
                        + item["SeriesName"]
                        + " - "
                        + get_season_episode(
                            item["ParentIndexNumber"], item["IndexNumber"]
                        )
                        + " - "
                        + item["Name"]
                        + " - "
                        + get_days_since_watched(item["UserData"]["LastPlayedDate"])
                        + " - Favorite: "
                        + str(itemIsFav)
                        + " - "
                        + "EpisodeID: "
                        + item["Id"]
                    )
                except (KeyError):
                    item_details = "  {Type} - {Name} - {Id}".format(**item)
                    if bool(cfg.DEBUG):
                        # DEBUG
                        print("\nError encountered - Keep Episode: \n" + str(item))
                print(":[KEEPING] - " + item_details)
        elif item["Type"] == "Video":
            if (
                (item["Type"] == "Video")
                and (cfg.not_played_age_video >= 0)
                and (item["UserData"]["PlayCount"] >= 1)
                and (cut_off_date_video > parse(item["UserData"]["LastPlayedDate"]))
                and (
                    not bool(cfg.keep_favorites_video)
                    or not item["UserData"]["IsFavorite"]
                )
            ):
                try:
                    item_details = (
                        item["Type"]
                        + " - "
                        + item["Name"]
                        + " - "
                        + get_days_since_watched(item["UserData"]["LastPlayedDate"])
                        + " -  Favorite: "
                        + str(item["UserData"]["IsFavorite"])
                        + " - "
                        + "VideoID: "
                        + item["Id"]
                    )
                except (KeyError):
                    item_details = "  {Type} - {Name} - {Id}".format(**item)
                    if bool(cfg.DEBUG):
                        # DEBUG
                        print("\nError encountered - Delete Video: \n" + str(item))
                print(":*[DELETE] - " + item_details)
                deleteItems.append(item)
            else:
                try:
                    item_details = (
                        item["Type"]
                        + " - "
                        + item["Name"]
                        + " - "
                        + get_days_since_watched(item["UserData"]["LastPlayedDate"])
                        + " - Favorite: "
                        + str(item["UserData"]["IsFavorite"])
                        + " - "
                        + "VideoID: "
                        + item["Id"]
                    )
                except (KeyError):
                    item_details = "  {Type} - {Name} - {Id}".format(**item)
                    if bool(cfg.DEBUG):
                        # DEBUG
                        print("\nError encountered - Keep Video: \n" + str(item))
                print(":[KEEPING] - " + item_details)
        elif item["Type"] == "Trailer":
            if (
                (cfg.not_played_age_trailer >= 0)
                and (item["UserData"]["PlayCount"] >= 1)
                and (cut_off_date_trailer > parse(item["UserData"]["LastPlayedDate"]))
                and (
                    not bool(cfg.keep_favorites_trailer)
                    or not item["UserData"]["IsFavorite"]
                )
            ):
                try:
                    item_details = (
                        item["Type"]
                        + " - "
                        + item["Name"]
                        + " - "
                        + get_days_since_watched(item["UserData"]["LastPlayedDate"])
                        + " -  Favorite: "
                        + str(item["UserData"]["IsFavorite"])
                        + " - "
                        + "TrailerID: "
                        + item["Id"]
                    )
                except (KeyError):
                    item_details = "  {Type} - {Name} - {Id}".format(**item)
                    if bool(cfg.DEBUG):
                        # DEBUG
                        print("\nError encountered - Delete Trailer: \n" + str(item))
                print(":*[DELETE] - " + item_details)
                deleteItems.append(item)
            else:
                try:
                    item_details = (
                        item["Type"]
                        + " - "
                        + item["Name"]
                        + " - "
                        + get_days_since_watched(item["UserData"]["LastPlayedDate"])
                        + " - Favorite: "
                        + str(item["UserData"]["IsFavorite"])
                        + " - "
                        + "TrailerID: "
                        + item["Id"]
                    )
                except (KeyError):
                    item_details = "  {Type} - {Name} - {Id}".format(**item)
                    if bool(cfg.DEBUG):
                        # DEBUG
                        print("\nError encountered - Keep Trailer: \n" + str(item))
                print(":[KEEPING] - " + item_details)
        else:  # (item['Type'] == 'Unknown')
            try:
                item_details = (
                    item["Type"]
                    + " - "
                    + item["Name"]
                    + " - Favorite: "
                    + str(item["UserData"]["IsFavorite"])
                    + " - ID: "
                    + item["Id"]
                )
            except (KeyError):
                item_details = "  {Type} - {Name} - {Id}".format(**item)
                if bool(cfg.DEBUG):
                    # DEBUG
                    print(
                        "\nError encountered - Keep Unknown Media Type: \n" + str(item)
                    )
            print(":[KEEPING UNKNOWN MEDIA TYPE] - " + item_details)

    if len(data["Items"]) <= 0:
        print("[NO WATCHED ITEMS]")

    print("-----------------------------------------------------------")
    print("\n")
    return deleteItems


def list_delete_items(deleteItems):
    # List items to be deleted
    print("-----------------------------------------------------------")
    print("Summary Of Deleted Media:")
    if not bool(cfg.remove_files):
        print("* Trial Run          *")
        print("* remove_files=0     *")
        print("* No Media Deleted   *")
    print("-----------------------------------------------------------")

    if len(deleteItems) > 0:
        for item in deleteItems:
            if item["Type"] == "Movie":
                item_details = "  {Type} - {Name} - {Id}".format(**item)
            elif item["Type"] == "Episode":
                try:
                    item_details = " - ".join(
                        [
                            item["Type"],
                            item["SeriesName"],
                            get_season_episode(
                                item["ParentIndexNumber"], item["IndexNumber"]
                            ),
                            item["Name"],
                            item["Id"],
                        ]
                    )
                except (KeyError):
                    item_details = "  {Type} - {Name} - {Id}".format(**item)
                    if bool(cfg.DEBUG):
                        # DEBUG
                        print("Error encountered - Delete Episode: \n\n" + str(item))
            elif item["Type"] == "Video":
                item_details = "  {Type} - {Name} - {Id}".format(**item)
            elif item["Type"] == "Trailer":
                item_details = "  {Type} - {Name} - {Id}".format(**item)
            else:  # item['Type'] == 'Unknown':
                pass
            delete_item(item["Id"])
            print("[DELETED] " + item_details)
    else:
        print("[NO ITEMS TO DELETE]")

    print("-----------------------------------------------------------")
    print("\n")
    print("-----------------------------------------------------------")
    print("Done.")
    print("-----------------------------------------------------------")


try:
    import media_cleaner_config as cfg

    test = cfg.DEBUG

    if (
        not hasattr(cfg, "server_brand")
        or not hasattr(cfg, "server_url")
        or not hasattr(cfg, "admin_username")
        or not hasattr(cfg, "admin_password_sha1")
        or not hasattr(cfg, "access_token")
        or not hasattr(cfg, "user_key")
        or not hasattr(cfg, "keep_favorites_movie")
        or not hasattr(cfg, "keep_favorites_episode")
        or not hasattr(cfg, "keep_favorites_video")
        or not hasattr(cfg, "keep_favorites_trailer")
        or not hasattr(cfg, "remove_files")
        or not hasattr(cfg, "not_played_age_movie")
        or not hasattr(cfg, "not_played_age_episode")
        or not hasattr(cfg, "not_played_age_video")
        or not hasattr(cfg, "not_played_age_trailer")  # or
    ):
        if (
            not hasattr(cfg, "server_brand")
            or not hasattr(cfg, "server_url")
            or not hasattr(cfg, "admin_username")
            or not hasattr(cfg, "admin_password_sha1")
            or not hasattr(cfg, "access_token")
            or not hasattr(cfg, "user_key")  # or
        ):

            if hasattr(cfg, "server_brand"):
                delattr(cfg, "server_brand")
            if hasattr(cfg, "server_url"):
                delattr(cfg, "server_url")
            if hasattr(cfg, "admin_username"):
                delattr(cfg, "admin_username")
            if hasattr(cfg, "admin_password_sha1"):
                delattr(cfg, "admin_password_sha1")
            if hasattr(cfg, "access_token"):
                delattr(cfg, "access_token")
            if hasattr(cfg, "user_key"):
                delattr(cfg, "user_key")

            print("-----------------------------------------------------------")
            server_brand = get_brand()

            print("-----------------------------------------------------------")
            server = get_url()
            print("-----------------------------------------------------------")
            port = get_port()
            print("-----------------------------------------------------------")
            server_base = get_base(server_brand)
            if len(port):
                server_url = server + ":" + port + "/" + server_base
            else:
                server_url = server + "/" + server_base
            print("-----------------------------------------------------------")

            username = get_admin_username()
            print("-----------------------------------------------------------")
            password = get_admin_password()
            password_sha1 = get_admin_password_sha1(password)
            print("-----------------------------------------------------------")

            auth_key = get_auth_key(server_url, username, password, password_sha1)
            user_key = list_users(server_url, auth_key)
            print("-----------------------------------------------------------")

        print("\n")
        print("-----------------------------------------------------------")
        print("ATTENTION!!!")
        print("Old or incomplete config in use.")
        print(
            "1) Delete media_cleaner_config.py and run this again to create a new config."
        )
        print("Or")
        print(
            "2) Delete DEBUG from media_cleaner_config.py and run this again to create a new config."
        )
        print("-----------------------------------------------------------")
        print("Matching value(s) in media_cleaner_config.py ignored.")
        print("Using the below config value(s) for this run:")
        print("-----------------------------------------------------------")

        if not hasattr(cfg, "server_brand"):
            print("server_brand='" + str(server_brand) + "'")
            setattr(cfg, "server_brand", server_brand)
        if not hasattr(cfg, "server_url"):
            print("server_url='" + str(server_url) + "'")
            setattr(cfg, "server_url", server_url)
        if not hasattr(cfg, "admin_username"):
            print("admin_username='" + str(username) + "'")
            setattr(cfg, "admin_username", username)
        if not hasattr(cfg, "admin_password_sha1"):
            print("admin_password_sha1='" + str(password_sha1) + "'")
            setattr(cfg, "admin_password_sha1", password_sha1)
        if not hasattr(cfg, "access_token"):
            print("access_token='" + str(auth_key) + "'")
            setattr(cfg, "access_token", auth_key)
        if not hasattr(cfg, "user_key"):
            print("user_key='" + str(user_key) + "'")
            setattr(cfg, "user_key", user_key)

        if not hasattr(cfg, "keep_favorites_movie"):
            print("keep_favorites_movie=1")
            setattr(cfg, "keep_favorites_movie", 1)
        if not hasattr(cfg, "keep_favorites_episode"):
            print("keep_favorites_episode=1")
            setattr(cfg, "keep_favorites_episode", 1)
        if not hasattr(cfg, "keep_favorites_video"):
            print("keep_favorites_video=1")
            setattr(cfg, "keep_favorites_video", 1)
        if not hasattr(cfg, "keep_favorites_trailer"):
            print("keep_favorites_trailer=1")
            setattr(cfg, "keep_favorites_trailer", 1)

        if not hasattr(cfg, "remove_files"):
            print("remove_files=0")
            setattr(cfg, "remove_files", 0)

        if not hasattr(cfg, "not_played_age_movie"):
            print("not_played_age_movie=100")
            setattr(cfg, "not_played_age_movie", 100)
        if not hasattr(cfg, "not_played_age_episode"):
            print("not_played_age_episode=100")
            setattr(cfg, "not_played_age_episode", 100)
        if not hasattr(cfg, "not_played_age_video"):
            print("not_played_age_video=100")
            setattr(cfg, "not_played_age_video", 100)
        if not hasattr(cfg, "not_played_age_trailer"):
            print("not_played_age_trailer=100")
            setattr(cfg, "not_played_age_trailer", 100)

        print("-----------------------------------------------------------")
        print("\n")

except (AttributeError, ModuleNotFoundError):
    generate_config()
    exit(0)

deleteItems = get_items(cfg.server_url, cfg.user_key, cfg.access_token)
list_delete_items(deleteItems)
