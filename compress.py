import copy
import json
import sys
import ast

sys.setrecursionlimit(10000)

def getJsonData(JsonFile):
    with open(JsonFile, encoding="utf8") as f:
        data = json.load(f)
    return data

def getJsonDataLineByLine(JsonFile):
    data = []
    i = 0
    with open(JsonFile) as f:
        for line in f:
            i += 1
            line = line.strip()
            if line[0] == '[':
                line = line[1:]
            elif line[-1] == ']':
                line = line[:-1]
            if line[-1] == ',':
                line = line[:-1]
            try:
                data.append(json.loads(line))
                if i%10000 == 0: print(i, "success")
            except:
                data.append('''{"classBodyDeclaration": ""}''')
                print(i, "failure")
                print(line)
    return data

def getJsonDataSafe(JsonFile):
    try:
        return getJsonData(JsonFile)
    except Exception as e:
        print(e)
        print("Loading JSON failed. Attempting safe method.")
        return getJsonDataLineByLine(JsonFile)

def dump_dict(data, name):
    with open(name, 'w', encoding="utf8") as f:
        json.dump(data, f)

def tree2code(tree, indentation):
    if 'type' in tree:
        code = tree['text'] + ' '
        if tree['text'] in [';', '{', '}']:
            code += '\n'
            if tree['text'] == '{':
                indentation += 1
            elif tree['text'] == '}':
                indentation -= 1
            code += '\t'*indentation
        return code, indentation
    else:
        root = list(tree.keys())[0]
        children = tree[root]
        code = ""
        for child in children:
            t, indentation = tree2code(child, indentation)
            code += t
        return code, indentation
    

def get_compressed_func():
    global compression_number
    compression_number += 1
    return "$F"+str(compression_number)

def build_n_compress(tree, build_dict):
    var_list = []
    global abstract_code_dict
    global num_to_compress
    
    if 'text' in tree:
        code = tree["text"] + " "
        #print("**:\t",code, 1)
        return (code, 1, 0, var_list)
    else:
        parent = list(tree.keys())[0]
        children = tree[parent]
        if len(children) == 0:
            return ("", 0, 0, [])
        
        code = ""
        leaf_count = 0
        id_count = 0
        
        if len(children) > 1:
            for child in children:
                (c, n, i, vl) = build_n_compress(child, build_dict)
                code += c
                leaf_count += n
                id_count += i
                var_list += [v for v in vl if v not in var_list]
                
            if (var_list and leaf_count - len(var_list) >= 4) or (not var_list and leaf_count > 1) :
                abstract_code = code.split()
                for i in range(len(abstract_code)):
                    if abstract_code[i] in var_list:
                        abstract_code[i] = "$id{}".format(var_list.index(abstract_code[i]))
                abstract_code = ' '.join(abstract_code)
                
                # Build the dictionary or compress the tree
                if build_dict:
                    if abstract_code not in abstract_code_dict:
                        compressed_func = get_compressed_func()
                        abstract_code_dict[abstract_code] = {
                            'count': 0, 
                            'compressed_name': compressed_func,
                            'num_params': len(var_list)
                        }
                    abstract_code_dict[abstract_code]['count'] += 1
                else:
                    # If the abstracted code is within the range, replace
                    # the children with a single leaf node containing whole code
                    # If the list is empty, only one token.
                    if abstract_code in abstract_code_keys[:num_to_compress]:
                        compressed_func = abstract_code_dict[abstract_code]['compressed_name']
                        compressed_func += ' ( ' +' , '.join(var_list)+' )' if var_list else ''
                        tree[parent] = [{"type": "compressed", "text": compressed_func}]
                        
            #print(parent, ":\t",code, leaf_count, id_count, var_list)
            return (code, leaf_count, id_count, var_list)
        
        if parent == "literal":
            child = children[0]
            child_text = child["text"]
            try:
                if child_text in ['null', 'true', 'false']:
                    pass
                elif type(ast.literal_eval(child_text)) == type("STRING"):
                    children[0]["text"] = "STRING00"
                elif type(ast.literal_eval(child_text)) == type(1):
                    children[0]["text"] = "INT00"
                elif type(ast.literal_eval(child_text)) == type(1.1):
                    children[0]["text"] = "FLOAT00"
            except:
                children[0]["text"] = "NUM00"
        elif parent == "primary" and 'type' in children[0]:
            id_count += 1
            text = children[0]["text"]
            if text not in var_list:
                var_list.append(text)
        elif parent == "variableDeclaratorId" and 'type' in children[0]:
            id_count += 1
            text = children[0]["text"]
            if text not in var_list:
                var_list.append(text)

        (code, leaf_count, i, vl) = build_n_compress(children[0], build_dict)
        id_count += i
        var_list += [v for v in vl if v not in var_list]
        
        #print(parent, ":\t",code, leaf_count, id_count, var_list)
        return (code, leaf_count, id_count, var_list)
    
abstract_code_dict = getJsonData('abstract_code_dict_1.5m.json')
abstract_code_keys = sorted(abstract_code_dict, key = lambda x:abstract_code_dict[x]['count'], reverse=True)
num_to_compress = 25000
#print(abstract_code_keys[num_to_compress], abstract_code_dict[abstract_code_keys[num_to_compress]])



n = int(sys.argv[1])

print("=====[",n,"]=====")

try:
    all_data = getJsonDataSafe("../csn_big_only_trees/csn_big_{}.json".format(n))
except Exception as e:
    print(e)
    print("Data csn_big_{}.json is corrupted.".format(n))

compressed_codes = []
for i in range(len(all_data)):
    if i%10000 == 0: print("[", i, "]") 
    try:
        tree_copy = copy.deepcopy(all_data[i])
        (code, leaf_count, id_count, var_list) = build_n_compress(tree_copy, False)
        code, _ = tree2code(tree_copy, 0)
    except Exception as e:
        # Write the data number and file name to another file for later investigation
        print(e)
        code = ""
    compressed_code = {"code": code}
    compressed_codes.append(compressed_code)
dump_dict(compressed_codes, "../csn_compressed_codes/csn_compressed_{}.json".format(n))
