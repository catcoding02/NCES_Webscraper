import requests
import re

def get_county_school_dist_page(county_name: str, state_name:str):
    state_name = {"01": 'Alabama', "02": 'Alaska', "04": 'Arizona',
"05": 'Arkansas', "06": 'California', "08": 'Colorado',
"09": 'Connecticut', "10": 'Delaware', "11": 'District of Columbia',
"12": 'Florida', "13": 'Georgia', "15": 'Hawaii', "16": 'Idaho',
"17": 'Illinois', "18": 'Indiana', "19": 'Iowa',
"20": 'Kansas', "21": 'Kentucky', "22": 'Louisiana',
"23": 'Maine', "24": 'Maryland', "25": 'Massachusetts',
"26": 'Michigan', "27": 'Minnesota', "28": 'Mississippi',
"29": 'Missouri', "30": 'Montana', "31": 'Nebraska',
"32": 'Nevada', "33": 'New Hampshire', "34": 'New Jersey',
"35": 'New Mexico', "36": 'New York', "37": 'North Carolina',
"38": 'North Dakota', "39": 'Ohio', "40": 'Oklahoma',
"41": 'Oregon', "42": 'Pennsylvania', "44": 'Rhode Island',
"45": 'South Carolina', "46": "South Dakota", "47": 'Tennessee',
"48": 'Texas', "49": 'Utah', "50": 'Vermont',
"51": 'Virginia', "53": 'Washington', "54": "West Virginia",
"55": 'Wisconsin', "56": 'Wyoming'
}
    county_school_dist_url = f"https://nces.ed.gov/ccd/districtsearch/district_list.asp?Search=1&details=1&State=25&County={county_name}&DistrictType=1&DistrictType=2&DistrictType=3&DistrictType=4&DistrictType=5&DistrictType=6&DistrictType=7&DistrictType=8&DistrictType=9&NumOfStudentsRange=more&NumOfSchoolsRange=more&DistrictPageNum=1"
def get_school_dist_page(district_id: str):
    """
    Gets school district school list page
    param: district_id: str: NCES District ID
    :return: Nothing
    """
    district_profile_url = f"https://nces.ed.gov/ccd/schoolsearch/school_list.asp?Search=1&DistrictID={district_id}"
    first_page = requests.get(district_profile_url).text
    with open("district_info.txt", "w") as district_info:
        district_info.write(first_page)
    num_of_pages = re.findall("<strong>&nbsp;&nbsp;Page <font color='#EDFFE8'>1&nbsp;of&nbsp;\d+", first_page)
    if num_of_pages:
        page_count = re.search('[0-9]+$', num_of_pages[0]).group(0)
    else:
        # for districts with 1 page, there is no text to display Page Number of Number, so page number is 1
        page_count = "1"
    if int(page_count) > 1:
        for page_num in range(2, int(page_count) + 1):
            add_page = requests.get(f"https://nces.ed.gov/ccd/schoolsearch/school_list.asp?Search=1&DistrictID={district_id}&SchoolPageNum={page_num}").text
            with open("district_info.txt", "a") as district_info:
                district_info.write(add_page)
        return

def get_school_eligibility(district_id: str, elig_list: list):
    """
    Gets number of students eligible for free and reduced lunch in each school in district
    param: district_id: str: NCES District ID
    param: elig_list: list to be appended with eligible student totals
    :return: Nothing
    """
    with open("district_info.txt", "r") as district_info:
        contents = district_info.read()
    # find links to all schools in district
    results = re.findall(rf"school_detail\.asp\?Search=1&DistrictID={district_id}.*?&ID={district_id}\d*", contents)
    for query_param in results:
        school_url = f"https://nces.ed.gov/ccd/schoolsearch/{query_param}"
        school_page = requests.get(school_url).text
        # For schools with eligible students between 1000-999999
        total_large = re.findall(r"<strong>Total<sup>1</sup>: </strong>\d,\d{3}", school_page)
        total_indep_large = re.findall("<strong>Free lunch eligible by Direct Certification<sup>2</sup>: </strong>\d,\d{3}", school_page)
        if bool(total_large):
            eligible_raw = re.search('[0-9]+,[0-9]+', total_large[0]).group(0)
            eligible = eligible_raw.replace(",", "")
            elig_list.append(int(eligible))
            continue
        if bool(total_indep_large):
            eligible_raw = re.search('[0-9]+,[0-9]+', total_indep_large[0]).group(0)
            eligible = eligible_raw.replace(",", "")
            elig_list.append(int(eligible))
            continue
        # For schools with eligible students between 1-999
        total = re.findall(r"<strong>Total<sup>1</sup>: </strong>\d+", school_page)
        if bool(total):
            eligible = re.match('.*?([0-9]+)$', total[0]).group(1)
            elig_list.append(int(eligible))
        else:
            total_indep = re.findall("<strong>Free lunch eligible by Direct Certification<sup>2</sup>: </strong>\d+", school_page)
            if total_indep:
                eligible = re.match('.*?([0-9]+)$', total_indep[0]).group(1)
                if eligible == "0":
                    print("This school has not provided data. Skipping school...")
                    continue
                else:
                    elig_list.append(int(eligible))
    return

def calculate_percent_elig(district_id: str, total_list: list, elig_list: list, county_agg: str):
    """
    :param district_id: str: NCES District ID
    :param total_list: list: list to be appended with total students in each school in district
    :param elig_list: list: list to be appended with total eligible students in each school in district
    :param county_agg: str: User response indicating yes or no for county aggregation
    :param total_number_of_eligible_students_in_county: list: list holding all counts of eligible schools for districts entered
    :param total_number_of_schools_in_county: list: list holding all total students in schools for districts entered
    :return: Nothing
    """
    with open("district_info.txt", "r") as district_info:
        contents = district_info.read()
    # find links to all schools in district
    results = re.findall(rf"school_detail\.asp\?Search=1&DistrictID={district_id}.*?&ID={district_id}\d*", contents)
    total_number_of_schools = len(results)
    for query_param in results:
        school_url = f"https://nces.ed.gov/ccd/schoolsearch/{query_param}"
        school_page = requests.get(school_url).text
        total_students_find_large = re.findall("<td align=\"left\"><strong><font size=\"2\">Total Students:</font></strong></td>\r\n\t\t<td><img border=\"0\" src=\"/ccd/commonfiles/images/spacer\.gif\" width=\"4\" height=\"10\"></td>\r\n\t\t<td align=\"right\"><font size=\"3\">[0-9]+,[0-9]+", school_page)
        total_students_find = re.findall(
            "<td align=\"left\"><strong><font size=\"2\">Total Students:</font></strong></td>\r\n\t\t<td><img border=\"0\" src=\"/ccd/commonfiles/images/spacer\.gif\" width=\"4\" height=\"10\"></td>\r\n\t\t<td align=\"right\"><font size=\"3\">[0-9]+",
            school_page)
        # for schools with total students 1000-999999
        if bool(total_students_find_large):
            total_students_raw = re.search('[0-9]+,[0-9]+', total_students_find_large[0]).group(0)
            total_students = total_students_raw.replace(",", "")
            total_list.append(int(total_students))
        # for schools with students from 1-999
        elif bool(total_students_find):
            total_students = re.search('([0-9]+)$', total_students_find[0]).group(1)
            if total_students == "0":
                print("This school has has not reported data. Skipping...")
                continue
            else:
                total_list.append(int(total_students))
        else:
            print("Cannot find total students enrolled...exiting program")
            return
    count = 0
    # check lengths of both lists to ensure that no school data is missing
    if len(elig_list) == len(total_list):
        for index,elig_number in enumerate(elig_list):
            percent = elig_number / total_list[index]
            if percent >= 0.7:
                count += 1
        if county_agg == "1":
            write_to_total_files("total_elig_schools.txt", str(count))
            write_to_total_files("total_schools.txt", str(total_number_of_schools))
        percent_qual = (count / total_number_of_schools) * 100
        print(f"{percent_qual:.2f}% of schools in this district meet or exceed 70% or more students participating in the National School Lunch Program.")
    else:
        print("Some school data is missing. Operation cannot be completed at this time.")
    return

def write_to_total_files(total_filename, value):
    with open(total_filename, "a") as total:
        total.write(value + "\n")
def clear_file(filename):
    """
    Clears district info text from last use of program
    :param district_info: file: File containing district info
    :return: Nothing
    """
    with open(filename, "w") as clear_file:
        clear_file.write("")

def progress():
    """
    Print 'working' text for comfortable user experience
    :return:
    """
    print("Working...")
    return

def main():
    elig = []
    total = []
    new_user = input("Is this a new entry? Y or N: ")
    if new_user == "Y":
        clear_file("total_schools.txt")
        clear_file("total_elig_schools.txt")
    county_agg = input("Are you planning to report for a whole county (option 1) or a single district (option 2)? Choose option 1 or 2: ")
    district_id = input("What is the NCES District ID? ")
    dist_info = get_school_dist_page(district_id)
    progress()
    get_school_eligibility(district_id, elig)
    progress()
    calculate_percent_elig(district_id, total, elig, county_agg)




