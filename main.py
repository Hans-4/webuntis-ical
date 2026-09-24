import datetime
import pytz
from ics import Calendar, Event
import webuntis
from webuntis.objects import KlassenObject

import config

class Main:
    def __init__(self):
         self.s = webuntis.Session(
            username=config.username,
            password=config.password,
            server=config.server,
            school=config.school,
            useragent=config.useragent,
        ).login()

    @staticmethod
    def date_converter():
        start_date = config.startDate
        end_date = config.endDate
        datetime_format = '%d.%m.%Y'

        start_datetime = datetime.datetime.strptime(start_date, datetime_format)
        end_datetime = datetime.datetime.strptime(end_date, datetime_format)

        return start_datetime, end_datetime

    def get_initial_data(self):
        school_year = config.schoolYear if config.schoolYear is not None else self.s.schoolyears().current

        klass = self.s.klassen().filter(name=config.klass)[0]

        return klass, school_year

    def get_timetable(self, klass: KlassenObject, start, end, calendar: Calendar):
        timetable = self.s.timetable(klasse=klass, start=start, end=end).combine(combine_breaks=True)
        for i in range(len(timetable)):
            if timetable[i].code == "cancelled":
                continue
            if not timetable[i].subjects:
                continue

            subject = timetable[i].subjects[0]

            if not subject._data.get("active", True):
                continue

            subject_name = subject.long_name
            subject_short = subject.name

            subject_filter = self.filter_subject(subject_short)

            if subject_filter:
                location = ''
                try:
                    if len(timetable[i].rooms) == 1:
                        location = timetable[i].rooms[0].name
                    elif len(timetable[i].rooms) > 1:
                        location = ', '.join(r.name for r in timetable[i].rooms)
                except IndexError:
                    try:
                        location_list = timetable[i].original_rooms
                        if not location_list:
                            location = None

                        else:
                            location = ''.join(str(s) for s in location_list)
                    except IndexError:
                        location = ''
                        print(f"No room for {subject_name} found")

                start = self.apply_utc(timetable[i].start)
                end = self.apply_utc(timetable[i].end)
                attendees = timetable[i].klassen

                attendees = {kl.name for kl in attendees}

                if len(subject_name) > 0:
                    self.create_ics(calendar, subject_name, location, attendees, start, end)

            else:
                pass

    @staticmethod
    def apply_utc(local_time):
        local = pytz.timezone(config.timezone)
        local_dt = local.localize(local_time, is_dst=None)
        utc_dt = local_dt.astimezone(pytz.utc)

        return utc_dt

    @staticmethod
    def filter_subject(subject_short: str):
        config_subjects = config.subjects

        if not config_subjects:
            return True

        else:
            if subject_short in config_subjects:
                return True
            else:
                return False

    @staticmethod
    def create_ics(calendar: Calendar, subject: str, location: str|None, attendees: set|None, start, end):
        event = Event()
        event.name = subject
        if location is not None:
            event.location = location

        if attendees is not None:
            event.attendees = attendees

        event.begin = start
        event.end = end

        calendar.events.add(event)

    @staticmethod
    def save_ics(calendar):
        with open(config.ics_location + "file.ics", "w") as f:
            f.write(calendar.serialize())


    def run(self):
        start, end = self.date_converter()
        klass, school_year = self.get_initial_data()
        calendar = Calendar()

        self.get_timetable(klass, start, end, calendar)

        self.save_ics(calendar)
        self.s.logout()

if __name__ == '__main__':
    main = Main()
    main.run()