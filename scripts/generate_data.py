import argparse, csv, random
import h3

p=argparse.ArgumentParser()
p.add_argument("--rows",type=int,required=True)
p.add_argument("--output",required=True)
a=p.parse_args()

random.seed(42)
with open(a.output,"w",newline="") as f:
    w=csv.writer(f)
    w.writerow(["id","dataset","lat","lng","h3_res11","h3_res8","h3_res5","is_active","updated_at"])
    for i in range(1,a.rows+1):
        lat=random.uniform(13.45,13.90)
        lng=random.uniform(100.25,100.95)
        c=h3.latlng_to_cell(lat,lng,11)
        w.writerow([i,"synthetic",lat,lng,c,h3.cell_to_parent(c,8),h3.cell_to_parent(c,5),i%97!=0,"2026-09-29T00:00:00+00:00"])
