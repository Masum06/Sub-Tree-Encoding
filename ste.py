import subprocess, json
import ast
import json
import copy
import os
import sys
import zipfile

def add_class(method):
    return "public class Test {\n"+method+"\n}"

def remove_class(parse_tree):
    return {'classbody': parse_tree['compilationUnit'][0]['typeDeclaration'][1]['classDeclaration'][2]['classBody'][1:-1]}

def parse(code):
    code = add_class(code)
    tree = subprocess.check_output(['java', '-jar', 'mavenproject1-1.0-SNAPSHOT-jar-with-dependencies.jar', code])
    tree = json.loads(tree)
    tree = remove_class(tree)
    return tree

def getJsonData(JsonFile):
    try:
        with open(JsonFile, encoding="utf8") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print("JSON not found. Loading .ZIP")
        lastdot = JsonFile.rfind(".")
        ZipFile = JsonFile[:lastdot] + ".zip"
        #current_os = sys.platform
        lastslash = JsonFile.rfind("/")
        if lastslash == -1:
            targetdir = ""
        else:
            targetdir = JsonFile[:lastslash]
        try:
            with zipfile.ZipFile(ZipFile,"r") as zip_ref:
                zip_ref.extractall(targetdir)
        except FileNotFoundError:
            print("ERROR! ZIP File not found.")
        try:
            with open(JsonFile, encoding="utf8") as f:
                data = json.load(f)
            os.remove(JsonFile)
            return data
        except FileNotFoundError:
            print("ERROR! JSON File not found.")

def dump_dict(data, JsonFile):
    with open(JsonFile, 'w', encoding="utf8") as f:
        json.dump(data, f)
    file_size = os.path.getsize(JsonFile)
    if file_size//10**6 >= 100:
        lastdot = JsonFile.rfind(".")
        ZipFile = JsonFile[:lastdot]+ ".zip"
        
        zipfile.ZipFile(ZipFile, mode='w').write(JsonFile, compress_type=zipfile.ZIP_DEFLATED)
        os.remove(JsonFile)
        zip_size = os.path.getsize(ZipFile)
        if zip_size//10**6 >= 100:
            print("WARNING!!! File zipped, but still larger than 100MB.")
        else:
            print("""File larger than 100MB, Zipped for git.\n\
Previous size: {}MB Current size: {}MB.""".format(file_size//10**6, zip_size//10**6))


            
def tree2code(tree, indentation):
    code = ""
    parent = list(tree.keys())[0]
    children = tree[parent]
    if 'type' in tree:
        code = tree['text'] + ' '
        if tree['text'] in [';', '{', '}']:
            code += '\n'
            if tree['text'] == '{':
                indentation += 1
            elif tree['text'] == '}':
                indentation -= 1
            code += '\t'*indentation
        #return code, indentation
    elif len(children)==1 and parent == "literal":
        child = children[0]
        child_text = child["text"]
        #type(ast.literal_eval(child_text))
        try:
            if child_text in ['null', 'true', 'false']:
                code = child_text + " "
            elif type(ast.literal_eval(child_text)) == type("STRING"):
                code = "STRING00 "
            elif type(ast.literal_eval(child_text)) == type(1):
                code = "INT00 "
            elif type(ast.literal_eval(child_text)) == type(1.1):
                code = "FLOAT00 "
        except:
            code = "NUM00 "
    else:
        root = list(tree.keys())[0]
        children = tree[root]
        for child in children:
            t, indentation = tree2code(child, indentation)
            code += t
    return code, indentation

def get_compressed_func():
    global compression_number
    compression_number += 1
    return "$F"+str(compression_number)

def build_dict(tree):
    var_list = []
    global abstract_code_dict_copy
    global abstract_code_keys
    
    if 'text' in tree:
        code = tree["text"] + " "
        #print("**:\t",code, 1)
        return (code, 1, 0, [], None)
    else:
        parent = list(tree.keys())[0]
        children = tree[parent]
        if len(children) == 0:
            return ("", 0, 0, [], None)
        
        code = ""
        compressed_func = None
        leaf_count = 0
        id_count = 0
        children_list = []
        
        if len(children) > 1:
            for child in children:
                (c, n, i, vl, f) = build_dict(child)
                code += c
                leaf_count += n
                id_count += i
                var_list += [v for v in vl if v not in var_list]
                if f: children_list.append(f)
                #else: leaf_list += code.split()
                
            if (var_list and leaf_count - len(var_list) >= 4) or (not var_list and leaf_count > 1) :
                abstract_code = code.split()
                for i in range(len(abstract_code)):
                    if abstract_code[i] in var_list:
                        abstract_code[i] = "$id{}".format(var_list.index(abstract_code[i]))
                abstract_code = ' '.join(abstract_code)
                
                if abstract_code not in abstract_code_dict:
                    compressed_func = get_compressed_func()
                    abstract_code_dict[abstract_code] = {
                        'count': 0, 
                        'compressed_name': compressed_func,
                        'num_params': len(var_list),
                        'children': children_list,
                        #'leaves': leaf_list
                    }
                else:
                    compressed_func = abstract_code_dict[abstract_code]['compressed_name']
                
                abstract_code_dict[abstract_code]['count'] += 1
#                 children_list.insert(0, compressed_func)
                
            return (code, leaf_count, id_count, var_list, compressed_func)
        
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
            code = children[0]["text"] + " "
        elif parent == "primary" and 'type' in children[0]:
            id_count += 1
            text = children[0]["text"]
            if text not in var_list:
                var_list.append(text)
            code = text + " "
        elif parent == "variableDeclaratorId" and 'type' in children[0]:
            id_count += 1
            text = children[0]["text"]
            if text not in var_list:
                var_list.append(text)
            code = text + " "
        else:
            (code, leaf_count, i, vl, compressed_func) = build_dict(children[0])
            id_count += i
            var_list += [v for v in vl if v not in var_list]
        
        return (code, leaf_count, id_count, var_list, compressed_func)
    
def compress(tree):
    var_list = []
    global abstract_code_dict_copy
    global abstract_code_keys
    
    if 'text' in tree:
        code = tree["text"] + " "
        #print("**:\t",code, 1)
        return (code, 1, 0, [])
    else:
        parent = list(tree.keys())[0]
        children = tree[parent]
        if len(children) == 0:
            return ("", 0, 0, [])
        
        code = ""
        compressed_func = None
        leaf_count = 0
        id_count = 0
        children_list = []
        
        if len(children) > 1:
            for child in children:
                (c, n, i, vl) = compress(child)
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
                
                #---------------------------------------------------
                if abstract_code in abstract_code_keys:
                    compressed_func = abstract_code_dict_copy[abstract_code]['compressed_name']
                    compressed_func += ' ( ' +' , '.join(var_list)+' )' if var_list else ''
                    tree[parent] = [{"type": "compressed", "text": compressed_func}]
                #---------------------------------------------------

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
            code = children[0]["text"] + " "
            
        elif parent == "primary" and 'type' in children[0]:
            id_count += 1
            text = children[0]["text"]
            if text not in var_list:
                var_list.append(text)
            code = text + " "
        elif parent == "variableDeclaratorId" and 'type' in children[0]:
            id_count += 1
            text = children[0]["text"]
            if text not in var_list:
                var_list.append(text)
            code = text + " "
        else:
            (code, leaf_count, i, vl) = compress(children[0])
            id_count += i
            var_list += [v for v in vl if v not in var_list]
        
        return (code, leaf_count, id_count, var_list)


