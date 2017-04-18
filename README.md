# This repository is longer maintained. Consider using <https://github.com/kennytm/lproj2es> instead.

-----

This is a tool to convert the Apple Glossaries `*.dmg` into a single SQLite database for easy searching.

# Requirements

* An Apple ID, to download the `*.dmg`.
* Mac OS X, to read the `*.dmg`.
* Python 3.5+. Get it with [Homebrew](http://brew.sh/): `brew install python3`.

# Usage

1. Prepare for a download manager because there are so many `*.dmg` to retrieve. We recommend [DownThemAll!](http://www.downthemall.net/) with Firefox.
2. Go to https://developer.apple.com/downloads/?name=Glossaries, expand the "Glossaries - iOS" section.
3. Download all `*.dmg` files.
4. Run this script on all those `*.dmg`. The whole process takes about 19 minutes (roughly half a minute per language).

        ./convert_ios.py ~/Downloads/iOS_Localizations/*.dmg

5. The output can be read from `ios.sqlite`.

# Schema

The generated database contains two tables. The **Files** table lists all localized files recorded in the `*.dmg`. The **Localizations** table lists all translated strings.

```sql
CREATE TABLE Files (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    project TEXT NOT NULL,
    path    TEXT NOT NULL UNIQUE
);

CREATE TABLE Localizations (
    file_id     INTEGER NOT NULL,
    position    TEXT NOT NULL,
    description TEXT,
    en          TEXT NOT NULL,
    -- the rest list all translated languages
    ar          TEXT,
    ca          TEXT,
    ...
    zh_TW       TEXT,
    FOREIGN KEY(file_id) REFERENCES Files(id)
);
```

# Example queries

Find the translation of the word "Open" in French and German:

```sql
SELECT f.project, l.position, l.description, l.en, l.fr, l.de
FROM Localizations l
inner join Files f on f.id = l.file_id
WHERE l.en = 'Open';
```

