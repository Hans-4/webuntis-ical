import datetime
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
            if not timetable[i].subjects:
                continue
            subject = timetable[i].subjects[0].long_name
            subject_short = timetable[i].subjects[0].name

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
                        print(f"No room for {subject} found")

                start = timetable[i].start
                end = timetable[i].end

                if len(subject) > 0:
                    self.create_ics(calendar, subject, location, start, end)

            else:
                pass

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
    def create_ics(calendar: Calendar, subject: str, location: str|None, start, end):
        event = Event()
        event.name = subject
        if location is not None:
            event.location = location

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