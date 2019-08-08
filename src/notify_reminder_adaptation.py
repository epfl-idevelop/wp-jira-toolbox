from jira import JIRA
import settings
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jinja2 import Environment, select_autoescape, FileSystemLoader


def get_ready_sites_2018() -> list:
    jira = JIRA(settings.JIRA_URL, basic_auth=(settings.JIRA_USERNAME, settings.JIRA_PASSWORD))
    sites = jira.search_issues('project=WP2018 AND status in ("Adaptation PROD18", "Adaptations QA18") AND id<WP2018-158 AND (cf[10903] != "Pas de notif." OR cf[10903]=null)', maxResults=200)
    return sites


def transition_site() -> None:
    comment = "{}".format(site_name)
    print(comment)


def send_message(to: str, subject: str, message: str) -> None:
    me = settings.SMTP_FROM
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = me
    if settings.SMTP_DRYRUN:
        msg['To'] = me
        recipients = [me]
    else:
        msg['To'] = to
        recipients = [to, me]

    text = "Your mail client does not support HTML emails."

    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(message, 'html')

    msg.attach(part1)
    msg.attach(part2)

    smtp = smtplib.SMTP(settings.SMTP_SERVER)
    smtp.connect(settings.SMTP_SERVER)
    smtp.ehlo()
    smtp.starttls()
    smtp.ehlo()
    smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
    smtp.send_message(msg, me, recipients)
    smtp.quit()


def notify_webmasters(key: str, site_name: str, webmasters: str, wordpress_url: str, QA18_url:str, url_ventilation: str, QA_source: str) -> None:
    # time to buid the mails
    jinja_env = Environment(
        loader=FileSystemLoader("{}/templates/".format(os.path.dirname(os.path.dirname(__file__)))),
        autoescape=select_autoescape('html', 'xml'),
        trim_blocks=True,
        lstrip_blocks=True)

    jinja_template = jinja_env.get_template("20190807_reminder_adaptation.html")

    # Send the mail
    for webmaster in webmasters.split("|"):
        msgSubject = "[{0}] Passage à la nouvelle charte graphique - Transition to the new graphic charter".format(
            site_name)
        msgBody = jinja_template.render(site_name=site_name, webmasters=", ".join(webmasters.split("|")),
                                        WordPress_url=wordpress_url, QA18_url=QA18_url,
                                        url_ventilee=url_ventilation, QA_source=QA_source)
        send_message(webmaster, msgSubject, msgBody)

    jira = JIRA(settings.JIRA_URL, basic_auth=(settings.JIRA_USERNAME, settings.JIRA_PASSWORD))
    comment = "{}: Reminder : Notified '{}' to give us an answer to go live ".format(site_name, webmasters)
    jira.add_comment(key, comment)


if __name__ == "__main__":
    sites = get_ready_sites_2018()
    for site in sites:
        site_key = site.key
        site_name = site.fields.summary

        webmasters = site.fields.customfield_10403
        wordpress_url = site.fields.customfield_10501
        QA18_url = site.fields.customfield_10908
        url_ventilation = site.fields.customfield_10900
        QA_source = site.fields.customfield_10902 #tells if copy or empty site


        notify_webmasters(site_key, site_name, webmasters, wordpress_url, QA18_url, url_ventilation, str(QA_source))
        transition_site()