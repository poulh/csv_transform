import os
import re
from datetime import datetime
from datetime import timezone
from .Writer import Writer
from .Reader import Reader
#import pandas as pd


def create(df, transform, params):
    t = None
    if transform == 'print':
        t = Print(df, *params)

    if transform == 'print-columns':
        t = PrintColumnNames(df, *params)

    if transform == 'open':
        t = Open(df, *params)

    if transform == 'save':
        t = Save(df, *params)

    if transform == 'filter':
        t = Filter(df, *params)

    if transform == 'is-na':
        t = IsNa(df, *params)

    if transform == 'not-na':
        t = NotNa(df, *params)

    if transform == 'drop-column':
        t = DropColumn(df, *params)

    if transform == 'camelcase':
        t = CamelCase(df, *params)

    if transform == 'lower':
        t = Lower(df, *params)

    if transform == 'date-convert':
        t = DateConvert(df, *params)

    if transform == 'replace':
        t = Replace(df, *params)

    if transform == 'strip':
        t = Strip(df, *params)

    if transform == 'valid-email':
        t = ValidEmail(df, *params)

    if t is None:
        raise ValueError("unsupported transform '{}'".format(transform))

    return t


class Transform:
    def __init__(self, df, *params):
        self.df = df
        self.params = list(params)

    def transform(self):
        return self.df


class ColumnTransform(Transform):
    def __init__(self, df, *params):
        super().__init__(df, *params)
        self.column = self.params[0]


class CamelCase(Transform):
    def transform(self):
        def camel_case(word):

            try:
                word.index(' ')  # check for spaces
                parts = str.split(word)
                parts[0] = parts[0][0].lower() + parts[0][1:]
                parts[0] = parts[0].lower()
                return ''.join(parts)
            except ValueError:
                return word[0].lower() + word[1:]

        return self.df.rename(columns=camel_case)


class NotNa(ColumnTransform):
    def transform(self):

        return self.df[self.df[self.column].notna()]


class IsNa(ColumnTransform):
    def transform(self):

        return self.df[self.df[self.column].isna()]


class Filter(Transform):
    def transform(self):

        transform_name = self.params[0]
        #print("transform name: {}".format(transform_name))

        t = create(self.df.copy(), transform_name, self.params[1:])
        transformed_df = t.transform()

        transformed_df.set_index(t.column, inplace=True, drop=False)

        indexed_df = self.df.set_index(t.column, drop=False)

        results = indexed_df.drop(transformed_df.index, errors='ignore')

        return results.reset_index(drop=True)


class Lower(ColumnTransform):
    def transform(self):

        self.df[self.column] = self.df[self.column].map(
            lambda x: x.lower() if isinstance(x, str) else x)

        return self.df


class Strip(ColumnTransform):
    def transform(self):

        self.df[self.column] = self.df[self.column].map(
            lambda x: x.strip() if isinstance(x, str) else x)

        return self.df


class Replace(ColumnTransform):
    def transform(self):
        find = self.params[1]
        replace = self.params[2]
        self.df[self.column] = self.df[self.column].str.replace(find,
                                                                replace,
                                                                regex=False)

        return self.df


class Print(Transform):
    def transform(self):
        print(self.df)
        return super().transform()


class PrintColumnNames(Transform):
    def transform(self):
        print(self.df.columns)
        return super().transform()


class Open(ColumnTransform):
    def __init__(self, df, path, *params):
        #print("in open: {}".format(params))
        # the passed-in dataframe is the one from --path.  We are going to make our own
        # so we pass None up to the parent class and then set self.df via the Reader
        super().__init__(None, *params)

        r = Reader(path)
        self.df = r.read()
        print(self.params)


class Save(Transform):
    def transform(self):
        path = self.params[0]
        w = Writer(self.df, path)
        w.write()

        return super().transform()


class ValidEmail(ColumnTransform):
    def transform(self):
        # got this regex here: https://emailregex.com
        pattern = """(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9]))\.){3}(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9])|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])"""

        regex = re.compile(pattern)

        return self.df[self.df[self.column].str.match(pat=regex)]


class DateConvert(ColumnTransform):
    def __init__(self, df, *params):
        super().__init__(df, *params)
        self.strptime_format = self.params[1]
        self.strftime_format = self.params[2]

    def date_string_to_ymd(self, date_str):
        # print("converting '{}' using '{}' and '{}'".format(
        #     date_str, self.strptime_format, self.strftime_format))
        # clubhouse mongo format: "%Y-%m-%dT%H:%M:%S.%f%z"

        dt = datetime.strptime(date_str, self.strptime_format)
        local_dt = dt.replace(tzinfo=timezone.utc).astimezone(tz=None)
        local_date_str = local_dt.strftime(self.strftime_format)
        return local_date_str

    def transform(self):
        self.df[self.column] = self.df[self.column].apply(
            self.date_string_to_ymd)

        return self.df


class DropColumn(ColumnTransform):
    def transform(self):
        return self.df.drop(self.column, axis=1)
