from caldav import DAVClient

# 登录 iCloud CalDAV
client = DAVClient(
    url="https://caldav.icloud.com/",
    username="zgchung@outlook.com",
    password="cfxg-vtki-elza-btby",
)

principal = client.principal()

# 列出所有 calendar
calendars = principal.calendars()
for cal in calendars:
    print("Calendar:", cal.name)
