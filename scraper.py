import os.path
import re
import sys
import time
import urllib2


USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1599.101 Safari/537.36'
WRETCH_SEARCH = 'http://tw.blog.search.yahoo.com/search?fr=cb-wretch&type=web&provider=wretch&p={query}&xargs=0&pstart=1&b={start}'
YAHOO_SEARH = 'http://hk.blog.search.yahoo.com/search/blog?p={query}&ygmasrchbtn=blog+search&fr=uh-yblog&xargs=0&pstart=1&b={start}'


def main(query, data_dir):
    print('Starting search...')

    paginate(query, WRETCH_SEARCH, 'wretch', r'wretch\.cc/blog/([^/<?%]+)',
        data_dir)
    paginate(query, YAHOO_SEARH, 'yahoo', r'blog\.yahoo\.com/([^/<?%]+)',
        data_dir)


def paginate(query, template_url, name, pattern, data_dir):
    page = 1
    usernames = set()
    while True:
        print('{1} - Page {0}'.format(page, name))
        item_start = 10 * (page - 1) + 1
        content = search(template_url.format(query=query, start=item_start))

        for match in re.finditer(pattern, content):
            usernames.add(match.group(1))

        if 'id="pg-next"' in content:
            page += 1
        else:
            break

        time.sleep(1)

    path = '{0}.{1}.txt'.format(data_dir, name)
    with open(path, 'wb') as out_file:
        for username in usernames:
            out_file.write(username)
            out_file.write('\n')


def search(url):
    headers = {
        'User-Agent': USER_AGENT
    }

    while True:
        try:
            request = urllib2.Request(url, headers=headers)
            response = urllib2.urlopen(request)
            content = response.read()
        except urllib2.HTTPError as error:
            status_code = error.code
            content = error.read()
        else:
            status_code = response.getcode()

        if status_code != 200:
            print('Yahooed! (Error {0}). Sleeping.'.format(status_code))
            time.sleep(120)
        else:
            return content


if __name__ == '__main__':
    query = sys.argv[1]
    data_dir = sys.argv[2]
    main(query, data_dir)
