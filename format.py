import re
import os

bbl_path = r"./bdma.bbl"
bib_path = r"./bibbook.bib"
tex_path = r'./bdma.tex'
cite_cmd = 'cite'

if os.path.exists(bbl_path+".old"):
    print("Read from .old bbl file ? Default Y [Y/n]:")
    if input().upper()!="N":
        file = open(bbl_path+".old", "r")
        bbl_info = file.read()
        file.close()
    else: 
        file = open(bbl_path, "r")
        bbl_info = file.read()
        file.close()
else:
    file = open(bbl_path, "r")
    bbl_info = file.read()
    file.close()

file = open(bib_path, "r")
bib_info = file.read()
file.close()


file = open(tex_path, "r")
tex_info = file.read()
file.close()

# 1. Read author in bib
bib_dict = {}

def code_authors(_authors):
    rt = []
    for a in _authors:
        
        if a.find(",")>=0:
            gv, sur = a.split(",")
            gv, sur = gv.strip(), sur.strip()
            res = re.search(r'[A-Z]+',sur)
            # print(sur,res.start(),res.end(),len(sur))
            
            if res.end() == len(sur):
                out = ".".join(sur) + "." + " " + gv
            else:
                out = sur[0] + ". " + gv
        else: 
            out = a.strip()
        rt.append(out)
    if len(rt) == 1:
        res=rt[0]
    elif len(rt) == 2:
        res = rt[0] + " and " + rt[1]
    else:
        res = rt[0]
        for i in range(len(rt) - 2):
            res += " and " + rt[i+1]
        res += ", " + rt[-1]
    return res

bib_idx = []
re_bib_head = r'@[^{]*'
re_bib_author = r'author=\{[^\n]*\}'
for match in re.finditer(re_bib_head, bib_info):
    bib_idx += [match.start(),match.end()]
    # print("st match start index", match.start(), "End index", match.end())
bib_idx = bib_idx[1:]+[-1]

for i in range(len(bib_idx)//2):
    cont = bib_info[bib_idx[2*i] : bib_idx[2*i+1]]
    # print(cont)
    key = cont.split(",")[0][1:]
    author = re.search(re_bib_author, cont).group()[8:-1]
    # title = re.search(re_bib_title, cont).group()[7:-1]
    authors = author.split("and")
    cnt = len(authors)
    authors = code_authors(authors)
    # print(authors)
    bib_dict[key] = [authors,cnt]
    
# exit()

# 2. Refine bbl content
new_bbl = ""
re_bbl_head = r'\\begin\{thebibliography\}\{\d+\}'
re_bbl_tail = r'\\end\{thebibliography\}'
head_idx = re.search(re_bbl_head, bbl_info).end()
tail_idx = re.search(re_bbl_tail, bbl_info).start()
bbl_head = bbl_info[:head_idx]
bbl_tail = bbl_info[tail_idx:]

bbl_info = bbl_info[head_idx:tail_idx].strip()

re_bbl_item = r'\\bibitem\{'
bbl_idx = []


for match in re.finditer(re_bbl_item, bbl_info):
    bbl_idx += [match.start(),match.end()]
# bbl_head = bbl_info[:bbl_idx[0]]
# bbl_tail = bbl_info[bbl_idx[-1]:]

bbl_idx = bbl_idx[1:] + [-1]
bbl_dict={}

for i in range(len(bbl_idx)//2):
    cont = bbl_info[bbl_idx[2*i] : bbl_idx[2*i+1]].strip()
    cont = " ".join(cont.replace("\n"," ").split())
    key = cont.split("}")[0]
    fixed_author, cnt = bib_dict[key]
    if cnt <= 2:
        author_end = cont.find(",")
    else:
        i = 0
        for match in re.finditer(",", cont):
            if i < cnt-1:
                i += 1
                continue
            author_end = match.end()
            break
    bbl_dict[key] = [fixed_author,cont[author_end:]]
    # res= "\\bibitem{%s} \n %s%s \n\n"%(key,fixed_author,cont[author_end:])
    # new_bbl += res

# 3. Read texfile for used references
re_cite=r'\\%s\{[^{}]*\}'%cite_cmd

for match in re.finditer(re_cite, tex_info):
    key=tex_info[match.start():match.end()][6:-1]
    res= "\\bibitem{%s} \n %s%s \n\n"%(key,bbl_dict[key][0],bbl_dict[key][1])
    new_bbl += res

new_bbl = bbl_head + "\n\n" + new_bbl + "\n\n" + bbl_tail
bbl_info = bbl_head + "\n\n" + bbl_info + "\n\n" + bbl_tail
# print(new_bbl)
# print("*"*30)
# print(bbl_info)

# 3. Save olb bbl to .old one, and overwrite to bbl
# exit()

file = open(bbl_path+".old", "w")
file.write(bbl_info)
file.close()

file = open(bbl_path, "w")
file.write(new_bbl)
file.close()