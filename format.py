import re
import os

bbl_path = r"./bdma.bbl"
bib_path = r"./bibbook.bib"
tex_path = r'./bdma.tex'
cite_cmd = 'cite'
_cite_start_idx = len(cite_cmd) +2

if os.path.exists(bbl_path+".old"):
    print("Read from .old bbl file ? Default Y [Y/n]:")
    if input().upper()!="N":
        file = open(bbl_path+".old", "r", encoding='UTF-8')
        bbl_info = file.read()
        file.close()
    else: 
        file = open(bbl_path, "r", encoding='UTF-8')
        bbl_info = file.read()
        file.close()
else:
    file = open(bbl_path, "r", encoding='UTF-8')
    bbl_info = file.read()
    file.close()

file = open(bib_path, "r", encoding='UTF-8')
bib_info = file.read()
file.close()


file = open(tex_path, "r", encoding='UTF-8')
tex_info = file.read()
file.close()

# 1. Read author in bib
bib_dict = {}

def code_authors(_authors):
    rt = []
    for a in _authors:
        # print("|-","".join(a),"-|")
        a = a.strip()
        if a.find(",")>=0:
            sur, gv = a.split(",")
            sur, gv = sur.strip(), gv.strip()
            res = re.search(r'[A-Z.]+',gv)
            if res.end() == len(gv):
                out = ".".join(gv) + "." + " " + sur
            else:
                if gv[0] == "{":
                    # escape character like {\'c}
                    res = re.search(r'\{[^{}]*\}', gv) 
                    if res is None:
                        # {} words
                        res = re.search(r'\{[a-zA-Z]', gv)
                        out = gv[res.end()-1].upper() + ". " + sur
                    else:
                        out = gv[:res.end()].upper() + ". " + sur
                else:
                    out = gv[0].upper() + ". " + sur
        elif a.find(" ")>=0:
            blk_idx = a.index(" ")
            # sur, gv = a[blk_idx:].strip(), a[:blk_idx].strip()
            sur, gv = a[:blk_idx].strip(), a[blk_idx:].strip()
            # print(a)
            # print(sur,"||", gv)
            res = re.search(r'[A-Z]+',sur)
            if sur.find(".")>=0:
                print(sur, gv)
                out = sur + " " + gv
            elif res.end() == len(sur):
                out = ".".join(sur) + "." + " " + gv
            else:
                if gv[0] == "{":
                    # escape character like {\'c}
                    res = re.search(r'\{\\[^{}]*\}', gv) 
                    if res is None:
                        # {} words
                        res = re.search(r'\{[a-zA-Z]', gv)
                        out = gv[res.end()-1].upper() + ". " + sur
                    else:
                        out = gv[:res.end()].upper() + ". " + sur
                else:
                    out = gv[0].upper() + ". " + sur
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
            res += ", " + rt[i+1]
        res += " and " + rt[-1]
    return res

bib_idx = []
re_bib_head = r'@[^{]*'
re_bib_author = r'(?i)author\s*=\s*\{[^\n]*\n'
for match in re.finditer(re_bib_head, bib_info):
    bib_idx += [match.start(),match.end()]
    # print("st match start index", match.start(), "End index", match.end())
bib_idx = bib_idx[1:]+[-1]

for i in range(len(bib_idx)//2):
    cont = bib_info[bib_idx[2*i] : bib_idx[2*i+1]]
    # print(cont)
    key = cont.split(",")[0][1:]
    _res_author = re.search(re_bib_author, cont)    
    if _res_author is None:
        bib_dict[key] = [None,0]
    else:
        author = _res_author.group()
        author = author[author.index("{")+1:author.rindex("}")]
        authors = author.split(" and ")
        cnt = len(authors)
        authors = code_authors(authors)
        # if author.find("{")>=0:
        #     print(author)
        #     print("-"*30)
        #     print(authors)
        #     print("*"*30)
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
    # print(bbl_info[match.start():match.end()])
# bbl_head = bbl_info[:bbl_idx[0]]
# bbl_tail = bbl_info[bbl_idx[-1]:]
# exit()

bbl_idx = bbl_idx[1:] + [-1]
bbl_dict={}

for i in range(len(bbl_idx)//2):
    cont = bbl_info[bbl_idx[2*i] : bbl_idx[2*i+1]].strip()
    cont = " ".join(cont.replace("\n"," ").split())
    key = cont.split("}")[0]
    fixed_author, cnt = bib_dict[key]
    if cnt ==0:
        bbl_dict[key] = [None, cont.split("}")[1]]
        continue
    
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

# 3. Read texfile for used references
re_cite=r'\\%s\{[^{}]*\}'%cite_cmd
done = []

for match in re.finditer(re_cite, tex_info):
    keys=tex_info[match.start():match.end()][_cite_start_idx:-1]
    for key in keys.split(","):
        if key in done:
            continue
        done.append(key)
        key = key.strip()
        fixed_author, cnt = bbl_dict[key][0],bbl_dict[key][1]
        if fixed_author is None:
            res="\\bibitem{%s} \n %s \n\n"%(key,cnt)
        else:
            res= "\\bibitem{%s} \n %s%s \n\n"%(key,fixed_author, cnt)
        new_bbl += res
            

new_bbl = bbl_head + "\n\n" + new_bbl + "\n\n" + bbl_tail
bbl_info = bbl_head + "\n\n" + bbl_info + "\n\n" + bbl_tail
# print(new_bbl)
# print("*"*30)
# print(bbl_info)

# 3. Save olb bbl to .old one, and overwrite to bbl
# exit()

file = open(bbl_path+".old", "w", encoding='UTF-8')
file.write(bbl_info)
file.close()

file = open(bbl_path, "w", encoding='UTF-8')
file.write(new_bbl)
file.close()