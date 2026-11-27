# Buduje rastrowe warstwy hipsometryczne (paleta pastelowa) dla regionów generatora map konturowych.
import json, re, os, io, math, base64, sys, urllib.request
import numpy as np
from PIL import Image, ImageDraw
from pyproj import Proj
from scipy import ndimage

HERE = os.path.dirname(os.path.realpath(__file__))  # strona/skrypty
# Użycie (potrzebne: numpy, pillow, scipy, pyproj):
#   python3 skrypty/hipsometria.py            -> zapisuje strona/geografia/hipso/<region>.js
#   python3 skrypty/hipsometria.py pl eu      -> tylko wybrane regiony
GEN = os.path.join(HERE, '..', 'geografia', 'generator-map-konturowych.html')
_s = open(GEN, encoding='utf-8').read(); _i = _s.index('const REGIONS=') + len('const REGIONS=')
R = {r['k']: r for r in json.JSONDecoder().raw_decode(_s[_i:])[0]}
# odwzorowanie każdej mapy (LAEA) dopasowane do położenia miast: x = s*X + tx, y = -s*Y + ty
FIT = {"pl": [{"proj": "laea", "lon_0": 19.33490370705371, "lat_0": 52.66888714090518}, [0.0008686206671572106, 336.38439859423954, 241.34115429032357]], "eu": [{"proj": "laea", "lon_0": 15.018217666457707, "lat_0": 51.754872148779874}, [0.0001189100181733602, 277.6219812411395, 340.0163063120561]], "as": [{"proj": "laea", "lon_0": 90.11079629083444, "lat_0": 41.94376391195982}, [5.552207845846623e-05, 306.79157912391486, 302.18956258771175]], "af": [{"proj": "laea", "lon_0": 18.167704385050975, "lat_0": 3.379120323477074}, [7.50868383552534e-05, 366.6779478344579, 305.8524592791861]], "sa": [{"proj": "laea", "lon_0": -59.89436835909702, "lat_0": -18.39143567178038}, [9.2164192214068e-05, 355.64513952326524, 342.5963795307112]], "oc": [{"proj": "laea", "lon_0": 144.83301130763545, "lat_0": -24.73853496227566}, [8.779779925300261e-05, 301.6837250143621, 249.94741170165221]], "na": [{"proj": "laea", "lon_0": -99.95318617620345, "lat_0": 46.97517055501928}, [5.464192125759783e-05, 394.72019648666384, 275.33023286553237]]}
TILES = os.path.join(os.path.expanduser('~'), '.cache', 'hipso-tiles'); os.makedirs(TILES, exist_ok=True)
OUT = os.path.join(HERE, '..', 'geografia', 'hipso')
SC = 2  # piksele rastra na jednostkę viewBox
ZOOM = {'pl': 8, 'eu': 5, 'as': 4, 'af': 5, 'na': 5, 'sa': 5, 'oc': 5}
# klasy: [górna granica), kolor (z handoutu dla 6 klasy)
BREAKS = [0, 100, 200, 500, 1000, 2000, 3000]
COLS = ['#cfe3c6', '#dbeccf', '#e7f2cd', '#f4f3cd', '#f5e5c5', '#f0d2b6', '#e6bead', '#e0aaa8']  # depresja, 0-100, ..., >3000

def tile(z, x, y):
    x %= 2 ** z
    p = os.path.join(TILES, f'{z}_{x}_{y}.png')
    if not os.path.exists(p):
        urllib.request.urlretrieve(f'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png', p)
    a = np.asarray(Image.open(p).convert('RGB'), dtype=np.float32)
    return a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768

def sample(lon, lat, z):
    n = 2 ** z * 256
    lat = np.clip(lat, -85, 85)
    px = (lon + 180) / 360 * n
    py = (1 - np.log(np.tan(np.radians(lat)) + 1 / np.cos(np.radians(lat))) / math.pi) / 2 * n
    ok = np.isfinite(px)
    tx0, tx1 = int(np.floor(np.nanmin(px) / 256)), int(np.floor(np.nanmax(px) / 256))
    ty0, ty1 = int(np.floor(np.nanmin(py) / 256)), int(np.floor(np.nanmax(py) / 256))
    ty0 = max(ty0, 0); ty1 = min(ty1, 2 ** z - 1)
    print('  tiles', (tx1 - tx0 + 1) * (ty1 - ty0 + 1), flush=True)
    M = np.zeros(((ty1 - ty0 + 1) * 256, (tx1 - tx0 + 1) * 256), np.float32)
    for ty in range(ty0, ty1 + 1):
        for tx in range(tx0, tx1 + 1):
            M[(ty - ty0) * 256:(ty - ty0 + 1) * 256, (tx - tx0) * 256:(tx - tx0 + 1) * 256] = tile(z, tx, ty)
    M = ndimage.gaussian_filter(M, 1.0)
    cx = np.where(ok, px - tx0 * 256 - .5, 0); cy = np.where(ok, py - ty0 * 256 - .5, 0)
    v = ndimage.map_coordinates(M, [cy, cx], order=1, mode='nearest')
    return np.where(ok, v, np.nan)

def land_mask(r, W, H, paths=None):
    m = np.zeros((H, W), bool)
    for d in (paths if paths is not None else [l['d'] for l in r['land']]):
        one = np.zeros((H, W), bool)
        for sub in re.findall(r'M[^M]*', d):
            pts = [(float(a) * SC, float(b) * SC) for a, b in re.findall(r'(-?[\d.]+)[ ,](-?[\d.]+)', sub)]
            if len(pts) < 3: continue
            im = Image.new('1', (W, H), 0); ImageDraw.Draw(im).polygon(pts, fill=1)
            one ^= np.asarray(im, bool)
        m |= one
    return m

def build(k):
    r = R[k]; prm, (s, tx, ty) = FIT[k]
    W, H = int(r['w'] * SC), int(r['h'] * SC)
    xs = (np.arange(W) + .5) / SC; ys = (np.arange(H) + .5) / SC
    X, Y = np.meshgrid((xs - tx) / s, -(ys - ty) / s)
    lon, lat = Proj(prm)(X, Y, inverse=True)
    lon = np.where(np.abs(lon) > 1e20, np.nan, lon); lat = np.where(np.abs(lat) > 1e20, np.nan, lat)
    print(k, W, H, flush=True)
    e = sample(lon, lat, ZOOM[k])
    land = land_mask(r, W, H)
    # depresja tylko z dala od wybrzeża (nie myli się z niedokładnym brzegiem)
    dist = ndimage.distance_transform_edt(land)
    cls = np.digitize(np.nan_to_num(e, nan=0), BREAKS)  # 0 = <0, 1 = 0-100 ...
    dep = (cls == 0) & (dist > 3 * SC) & (e < -2)
    cls = np.where(cls == 0, 1, cls); cls = np.where(dep, 0, cls)
    cls = ndimage.median_filter(cls, 3)
    # rozlej kolory lądu na morze (krawędź przycina wektorowy obrys w SVG)
    grow = ndimage.binary_dilation(land, iterations=4 * SC)
    idx = ndimage.distance_transform_edt(~land, return_distances=False, return_indices=True)
    cls = np.where(land, cls, cls[idx[0], idx[1]])
    alpha = grow
    WATER = len(COLS)
    lakes = land_mask(r, W, H, r['lakes']) & land
    cls = np.where(lakes, WATER, cls)
    present = [int(i) for i in range(len(COLS)) if (cls[land] == i).sum() > 0.0005 * land.sum()]
    pal = []
    for c in COLS: pal += [int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)]
    pal += [0xd0, 0xde, 0xed, 255, 255, 255]
    T = len(COLS) + 1
    im = Image.fromarray(np.where(alpha, cls, T).astype(np.uint8), 'P')
    im.putpalette(pal)
    b = io.BytesIO(); im.save(b, 'PNG', optimize=True, transparency=T)
    # maska morza: tylko tam, gdzie poza lądem teren leży poniżej 0 m (lub tuż przy brzegu)
    sea = ndimage.binary_dilation(~land & (np.nan_to_num(e, nan=1) <= 0), iterations=3 * SC)
    sea |= ~land & (ndimage.distance_transform_edt(~land) <= 3 * SC)
    sea |= land
    ms = Image.fromarray(np.where(sea, 0, 1).astype(np.uint8), 'P'); ms.putpalette([0xd0, 0xde, 0xed, 255, 255, 255])
    bs = io.BytesIO(); ms.save(bs, 'PNG', optimize=True, transparency=1)
    print('  sea KB', len(bs.getvalue()) // 1024, flush=True)
    print('  png KB', len(b.getvalue()) // 1024, 'classes', present, flush=True)
    return {'png': 'data:image/png;base64,' + base64.b64encode(b.getvalue()).decode(),
            'sea': 'data:image/png;base64,' + base64.b64encode(bs.getvalue()).decode(), 'cls': present}

if __name__ == '__main__':
    ks = sys.argv[1:] or list(R)
    os.makedirs(OUT, exist_ok=True)
    for k in ks:
        d = build(k)
        with open(os.path.join(OUT, f'{k}.js'), 'w') as f:
            f.write('/* warstwa hipsometryczna – generowana skryptem skrypty/hipsometria.py (dane: Terrarium/Mapzen, AWS Open Data) */\n')
            f.write(f'(window.HIPSO=window.HIPSO||{{}})[{json.dumps(k)}]={json.dumps(d)};\n')
