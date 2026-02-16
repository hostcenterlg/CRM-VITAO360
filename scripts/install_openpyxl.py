import urllib.request, json, zipfile, io, sys

# Get correct URLs from PyPI
for pkg in ['et-xmlfile', 'openpyxl']:
    modname = pkg.replace('-', '_')
    try:
        __import__(modname)
        print(f'{modname} already installed')
        continue
    except ImportError:
        pass

    print(f'Fetching {pkg} info from PyPI...')
    url = f'https://pypi.org/pypi/{pkg}/json'
    data = json.loads(urllib.request.urlopen(url).read())

    whl_url = None
    for f in data['urls']:
        if f['filename'].endswith('.whl'):
            whl_url = f['url']
            break

    if not whl_url:
        print(f'  No wheel found for {pkg}!')
        continue

    print(f'  Downloading from {whl_url[:80]}...')
    resp = urllib.request.urlopen(whl_url)
    whl_data = resp.read()
    print(f'  Downloaded {len(whl_data)} bytes')

    sp = [p for p in sys.path if 'site-packages' in p][0]
    z = zipfile.ZipFile(io.BytesIO(whl_data))
    z.extractall(sp)
    print(f'  Installed {pkg} to {sp}')

import openpyxl
print(f'\nopenpyxl {openpyxl.__version__} ready!')
