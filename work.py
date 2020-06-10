from copy import deepcopy,copy


# Regex validation
def check_for_validation(regex):
    return validated_parenthesis(regex) and validated_signs(regex)


# check for parenthesis
def validated_parenthesis(regex):
    opened_parenthesis = 0
    for c in regex:
        if c == '(':
            opened_parenthesis += 1
        if c == ')':
            opened_parenthesis -= 1
        if opened_parenthesis < 0:
            print('ERROR missing parenthesis')
            return False
    if opened_parenthesis == 0:
        return True
    print('ERROR unclosed parenthesis')
    return False


# check for operators
def validated_signs(regex):
    for i, c in enumerate(regex):
        if c == '*':
            if i == 0:
                print('ERROR * missed argument at', i)
                return False
            if regex[i - 1] in '(|':
                print('ERROR * missed argument at', i)
                return False
        if c == '+':
            if i == 0:
                print('ERROR + missed argument at', i)
                return False
            if regex[i - 1] in '(|':
                print('ERROR + missed argument at', i)
                return False
        if c == '?':
            if i == 0:
                print('ERROR ? missed argument at', i)
                return False
            if regex[i - 1] in '(|':
                print('ERROR ? missed argument at', i)
                return False
        if c == '|':
            if i == 0 or i == len(regex) - 1:
                print('ERROR | missed argument at', i)
                return False
            if regex[i - 1] in '(|':
                print('ERROR | missed argument at', i)
                return False
            if regex[i + 1] in ')|':
                print('ERROR | missed argument at', i)
                return False
    return True


class RegexNode:

    @staticmethod
    def trim_parenthesis(regex):
        while regex[0] == '(' and regex[-1] == ')' and check_for_validation(regex[1:-1]):
            regex = regex[1:-1]
        return regex

    @staticmethod
    def is_concat(c):
        return c == '(' or RegexNode.is_letter(c)

    @staticmethod
    def is_letter(c):
        return c in alphabet

    def __init__(self, regex):
        self.nullable = None
        self.firstpos = []
        self.lastpos = []
        self.item = None
        self.position = None
        self.children = []

        if DEBUG:
            print('Current : ' + regex)
        # Check if it is leaf
        if len(regex) == 1 and self.is_letter(regex):
            # Leaf
            self.item = regex
            return

        # It is an internal node
        # Finding the leftmost operators in all tree
        kleene = -1
        or_operator = -1
        concatenation = -1
        plus = -1
        question = -1
        i = 0

        # Getting the rest of terms
        while i < len(regex):
            if regex[i] == '(':
                # Composed block
                bracketing_level = 1
                # Skipping the entire term
                i += 1
                while bracketing_level != 0 and i < len(regex):
                    if regex[i] == '(':
                        bracketing_level += 1
                    if regex[i] == ')':
                        bracketing_level -= 1
                    i += 1
            else:
                # Going to the next char
                i += 1

            # Found a concat at previous iteration
            # And also it was the last element check if breaking
            if i == len(regex):
                break

            # Testing if concat
            if self.is_concat(regex[i]):
                if concatenation == -1:
                    concatenation = i
                continue
            # Testing for kleene
            if regex[i] == '*':
                if kleene == -1:
                    kleene = i
                continue
            # Testing for plus
            if regex[i] == '+':
                if plus == -1:
                    plus = i
                continue
            # Testing for question
            if regex[i] == '?':
                if question == -1:
                    question = i
                continue
            # Testing for <or> operator
            if regex[i] == '|':
                if or_operator == -1:
                    or_operator = i
        # Setting the current operation by priority
        if or_operator != -1:
            # Found an or operation
            self.item = '|'
            self.children.append(RegexNode(self.trim_parenthesis(regex[:or_operator])))
            self.children.append(RegexNode(self.trim_parenthesis(regex[(or_operator + 1):])))
        elif concatenation != -1:
            # Found a concatenation
            self.item = '.'
            self.children.append(RegexNode(self.trim_parenthesis(regex[:concatenation])))
            self.children.append(RegexNode(self.trim_parenthesis(regex[concatenation:])))
        elif kleene != -1:
            # Found a kleene
            self.item = '*'
            self.children.append(RegexNode(self.trim_parenthesis(regex[:kleene])))
        elif plus != -1:
            # Found a plus
            self.item = '+'
            self.children.append(RegexNode(self.trim_parenthesis(regex[:plus])))
        elif question != -1:
            # Found a question
            self.item = '?'
            self.children.append(RegexNode(self.trim_parenthesis(regex[:question])))

    def calc_functions(self, pos, followpos):
        if self.is_letter(self.item):
            # Is a leaf
            self.firstpos = [pos]
            self.lastpos = [pos]
            self.position = pos
            # Add the position in the followpos list
            followpos.append([self.item, []])
            return pos + 1
        # Is an internal node
        for child in self.children:
            pos = child.calc_functions(pos, followpos)
        # Calculate current functions

        if self.item == '.':
            # Is concatenation
            # Firstpos
            if self.children[0].nullable:
                self.firstpos = sorted(list(set(self.children[0].firstpos + self.children[1].firstpos)))
            else:
                self.firstpos = deepcopy(self.children[0].firstpos)
            # Lastpos
            if self.children[1].nullable:
                self.lastpos = sorted(list(set(self.children[0].lastpos + self.children[1].lastpos)))
            else:
                self.lastpos = deepcopy(self.children[1].lastpos)
            # Nullable
            self.nullable = self.children[0].nullable and self.children[1].nullable
            # Followpos
            for i in self.children[0].lastpos:
                for j in self.children[1].firstpos:
                    if j not in followpos[i][1]:
                        followpos[i][1] = sorted(followpos[i][1] + [j])

        elif self.item == '|':
            # Is or operator
            # Firstpos
            self.firstpos = sorted(list(set(self.children[0].firstpos + self.children[1].firstpos)))
            # Lastpos
            self.lastpos = sorted(list(set(self.children[0].lastpos + self.children[1].lastpos)))
            self.nullable = self.children[0].nullable or self.children[1].nullable

        elif self.item == '*':
            # Is kleene
            # Firstpos
            self.firstpos = deepcopy(self.children[0].firstpos)
            # Lastpos
            self.lastpos = deepcopy(self.children[0].lastpos)
            # Nullable
            self.nullable = True
            # Followpos
            for i in self.children[0].lastpos:
                for j in self.children[0].firstpos:
                    if j not in followpos[i][1]:
                        followpos[i][1] = sorted(followpos[i][1] + [j])

        elif self.item == '+':
            # Is plus
            # Firstpos
            self.firstpos = deepcopy(self.children[0].firstpos)
            # Lastpos
            self.lastpos = deepcopy(self.children[0].lastpos)
            # Nullable
            self.nullable = self.children[0].nullable
            # Followpos
            for i in self.children[0].lastpos:
                for j in self.children[0].firstpos:
                    if j not in followpos[i][1]:
                        followpos[i][1] = sorted(followpos[i][1] + [j])

        elif self.item == '?':
            # Is question
            # Firstpos
            self.firstpos = deepcopy(self.children[0].firstpos)
            # Lastpos
            self.lastpos = deepcopy(self.children[0].lastpos)
            # Nullable
            self.nullable = True

        return pos

    def write_level(self, level):
        print(str(level) + ' ' + self.item, self.firstpos, self.lastpos, self.nullable,
              '' if self.position == None else self.position)
        for child in self.children:
            child.write_level(level + 1)


class RegexTree:

    def __init__(self, regex):
        self.root = RegexNode(regex)
        self.followpos = []
        self.functions()

    def write(self):
        self.root.write_level(0)

    def functions(self):
        positions = self.root.calc_functions(0, self.followpos)
        if DEBUG == True:
            print(self.followpos)

    def toDfa(self):

        def contains_hashtag(q):
            for i in q:
                if self.followpos[i][0] == '#':
                    return True
            return False

        M = []  # Marked states
        Q = []  # States list in the followpos form ( array of positions )
        V = alphabet - {'#',''}  # Automata alphabet
        d = []  # Delta function, an array of dictionaries d[q] = {x1:q1, x2:q2 ..} where d(q,x1) = q1, d(q,x2) = q2..
        F = []  # FInal states list in the form of indexes (int)
        q0 = self.root.firstpos

        Q.append(q0)
        if contains_hashtag(q0):
            F.append(Q.index(q0))

        while len(Q) - len(M) > 0:
            # There exists one unmarked
            # We take one of those
            q = [i for i in Q if i not in M][0]
            # Generating the delta dictionary for the new state
            d.append({})
            # We mark it
            M.append(q)
            # For each letter in the automata's alphabet
            for a in V:
                # Compute destination state ( d(q,a) = U )
                U = []
                # Compute U
                # foreach position in state
                for i in q:
                    # if i has label a
                    if self.followpos[i][0] == a:
                        # We add the position to U's composition
                        U = U + self.followpos[i][1]
                U = sorted(list(set(U)))
                # Checking if this is a valid state
                if len(U) == 0:
                    # No positions, skipping, it won't produce any new states ( also won't be final )
                    continue
                if U not in Q:
                    Q.append(U)
                    if contains_hashtag(U):
                        F.append(Q.index(U))
                # d(q,a) = U
                d[Q.index(q)][a] = Q.index(U)

        return Dfa(Q, V, d, Q.index(q0), F)


class Dfa:

    def __init__(self, Q, V, d, q0, F):
        self.Q = Q
        self.V = V
        self.d = d
        self.q0 = q0
        self.F = F

    def run(self, text):
        # Checking if the input is in the current alphabet
        if len(set(text) - self.V) != 0:
            # Not all the characters are in the language
            print('ERROR characters', (set(text) - self.V), 'are not in the automate\'s alphabet')
            exit(0)

        # Running the automate
        q = self.q0
        for i in text:
            # Check if transition exists
            if q >= len(self.d):
                print('Message NOT accepted, state has no transitions')
                continue
            if i not in self.d[q].keys():
                print('Message NOT accepted, state has no transitions with the character')
                continue
            # Execute transition
            q = self.d[q][i]
        if q in self.F:
            print('Message accepted!')
        else:
            print('Message NOT accepted, stopped in an unfinal state')

    def write(self, identify):
        k = 0
        grammarString = ''
        listOfGrammarStrings = []
        for i in range(identify, len(self.Q)+identify):
            # Printing index, the delta function for that transition and if it's final state
            if i == identify:
                for name in self.d[k].keys():
                    if i == self.d[k][name]:
                        print('S -> ', name, 'A', self.d[k][name] + identify, '|e' if k in self.F else '',
                              sep='')
                        grammarString = ['S','-> ', name, 'A', self.d[k][name] + identify, '|e' if k in self.F else '']
                        listOfGrammarStrings.append(grammarString)
                    elif k + 1 < len(self.d):
                        if bool(self.d[k+1]):
                            print('S -> ', name, 'A', self.d[k][name]+identify, '|e' if k in self.F else '', sep='')
                            grammarString = ['S','-> ', name, 'A', self.d[k][name]+identify, '|e' if k in self.F else '']
                            listOfGrammarStrings.append(grammarString)
                        else:
                            print('S -> ', name, '|e' if k in self.F else '', sep='')
                            grammarString = ['S','-> ', name, '|e' if k in self.F else '']
                            listOfGrammarStrings.append(grammarString)
                k += 1
            else:
                for name in self.d[k].keys():
                    if i == self.d[k][name]:
                        print('A', i, ' -> ', name, 'A', self.d[k][name] + identify, '|e' if k in self.F else '',
                              sep='')
                        grammarString = ['A', i, ' -> ', name, 'A', self.d[k][name] + identify, '|e' if k in self.F else '']
                        listOfGrammarStrings.append(grammarString)
                    elif (k + 1 < len(self.d)) and bool(self.d[k+1]):
                        print('A', i, ' -> ', name, 'A', self.d[k][name] + identify, '|e' if k in self.F else '', sep='')
                        grammarString = ['A', i, ' -> ', name, 'A', self.d[k][name] + identify, '|e' if k in self.F else '']
                        listOfGrammarStrings.append(grammarString)
                    else:
                        print('A', i, ' -> ', name, '|e' if k in self.F else '', sep='')
                        grammarString = ['A', i, ' -> ', name, '|e' if k in self.F else '']
                        listOfGrammarStrings.append(grammarString)
                k += 1
        return listOfGrammarStrings


# Preprocessing Functions
def preprocess(regex):
    regex = clean_plus(regex)
    regex = clean_kleene(regex)
    regex = regex.replace(' ', '')
    regex = '(' + regex + ')' + '#'
    while '()' in regex:
        regex = regex.replace('()', '')
    return regex


def clean_plus(regex):
    for i in range(0, len(regex) - 1):
        while i < len(regex) - 1 and regex[i + 1] == regex[i] and regex[i] == '+':
            regex = regex[:i] + regex[i + 1:]
    return regex


def clean_kleene(regex):
    for i in range(0, len(regex) - 1):
        while i < len(regex) - 1 and regex[i + 1] == regex[i] and regex[i] == '*':
            regex = regex[:i] + regex[i + 1:]
    return regex


def gen_alphabet(regex):
    return set(regex) - set('()|+*?')


def first_method(reg1, reg2):
    listOfReg = []
    listOfI = []
    finalList = []
    if len(reg1)>len(reg2):
        lenReg = len(reg2)
        lenBigger = len(reg1)
    else:
        lenReg = len(reg1)
        lenBigger = len(reg2)
    # find equal transactions
    for i in range(lenBigger):
        if i < lenReg:
            if reg1[i][0] == 'S':
                if reg1[i][2] == reg2[i][2]:
                    listOfReg.append(copy(reg1[i]))
                    listOfI.append(i)
            else:
                if reg1[i][3] == reg2[i][3]:
                    listOfReg.append(copy(reg1[i]))
                    listOfI.append(i)
    # delete not sequenced transactions
    for i in range(len(listOfReg)):
            if i == 0:
                continue
            elif len(listOfReg[i]) == 7:
                if listOfReg[i][6]:
                    continue
            elif listOfReg[i][0] == 'S' or listOfReg[i][1] == listOfReg[i - 1][4] or listOfReg[i][1] == listOfReg[i - 1][5]:
                continue
            else:
                listOfReg.remove(listOfReg[i])
                listOfI.remove(listOfI[i])
    if len(listOfReg) == 1:
        listOfReg.clear()
        listOfI.clear()
    # swap terminals from listofReg to second reg
    j = 0
    for i in listOfI:
        reg2[i] = listOfReg[j]
        if i == 1 and len(reg2) != 3:
            reg2[i][1] = reg2[i-1][4]
        elif i == 0:
            pass
        elif i == len(reg2)-2:
            reg2[i+1][1] = reg2[i][5]
        elif j == len(listOfI)-1 and len(reg2)-1 != j:
            reg2[i][5] = reg2[i+1][1]
        elif j == 0:
            reg2[i][1] = reg2[i-1][5]
        j += 1
    # add two regexes in one list
    for i in range(len(reg1)):
        finalList.append(reg1[i])
    for i in range(len(reg2)):
        finalList.append(reg2[i])
    # make all elements unique
    uniquelist = []
    for i in range(len(finalList)):
        if finalList[i] not in uniquelist:
            uniquelist.append(finalList[i])
    return uniquelist
#Введите первое регулярное выражение
#b(a|b)ab*ca
#Введите второе регулярное выражение
#ba+bacca

def second_method(reg):
    listOfLastElements = []
    for i in range(len(reg)):
        if reg[i][0] == 'S':
            continue
        if reg[i][4] != 'A' and reg[i][4] != '|e':
            listOfLastElements.append(i)
    if len(listOfLastElements) > 0 and len(listOfLastElements) % 2 == 0:
        if reg[listOfLastElements[0]][3] == reg[listOfLastElements[1]][3]:
            reg[listOfLastElements[0] - 1][4] = 'C'
            reg[listOfLastElements[1] - 1][4] = 'C'
            reg[listOfLastElements[0] - 1][5] = '0'
            reg[listOfLastElements[1] - 1][5] = '0'
            reg[listOfLastElements[0]][0] = 'C'
            reg[listOfLastElements[0]][1] = '0'
            reg[listOfLastElements[1]][0] = 'C'
            reg[listOfLastElements[1]][1] = '0'
        else:
            reg[listOfLastElements[0]-1][3] = reg[listOfLastElements[0]-1][3] + reg[listOfLastElements[0]][3]
            reg[listOfLastElements[1]-1][3] = reg[listOfLastElements[1]-1][3] + reg[listOfLastElements[1]][3]
            reg[listOfLastElements[0]].clear()
            reg[listOfLastElements[1]].clear()
            reg[listOfLastElements[0] - 1][4] = ''
            reg[listOfLastElements[0] - 1][5] = ''
            reg[listOfLastElements[1] - 1][4] = ''
            reg[listOfLastElements[1] - 1][5] = ''
    uniquelist = []
    for i in range(len(reg)):
        if reg[i] not in uniquelist:
            uniquelist.append(reg[i])
    return uniquelist

def normal_print(reg):
    for i in range(len(reg)):
        if len(reg[i]) == 0:
            continue
        elif reg[i][0] == 'S':
            if len(reg[i]) == 4 :
                print(reg[i][0],reg[i][1],reg[i][2],reg[i][3], sep='')
            else:
                print(reg[i][0],reg[i][1],reg[i][2],reg[i][3],reg[i][4],reg[i][5], sep='')
        elif len(reg[i]) == 5:
            print(reg[i][0],reg[i][1],reg[i][2],reg[i][3],'|e' if len(reg[i]) == 5 and reg[i][4] == '|e' else '',sep ='')
        else:
            print(reg[i][0], reg[i][1], reg[i][2], reg[i][3], reg[i][4], reg[i][5], '|e' if len(reg[i]) == 7 and reg[i][6] == '|e' else '',sep ='')


# Settings
DEBUG = False


# Main
print('Введите первое регулярное выражение')
regex1 = input()
print('Введите второе регулярное выражение')
regex2 = input()
# Check
if not check_for_validation(regex1):
    exit(0)
if not check_for_validation(regex2):
    exit(0)

# Preprocessing regex and generate the alphabet
p_regex1 = preprocess(regex1)
p_regex2 = preprocess(regex2)
p_alphabet = p_regex1+p_regex2
alphabet = gen_alphabet(p_alphabet)

# add optional letters that don't appear in the expression
extra = ''

# Construct
tree1 = RegexTree(p_regex1)
if DEBUG:
    tree1.write()
dfa1 = tree1.toDfa()

tree2 = RegexTree(p_regex2)
if DEBUG:
    tree2.write()
dfa2 = tree2.toDfa()

# Test
message = 'cb'
print('Это первое регулярное выражение : ' + regex1)
print('Это второе регулярное выражение: ' + regex2)
print('Это входной алфавит : ' + ''.join(sorted(alphabet)))
# Operating with first regex
print('Это разбор первого регулярного выражения в к-с грамматике : \n')
myList = dfa1.write(0)
#for i in range(len(myList)):
#    print (myList[i])
fGLOBAL1 = dfa1.F
diction1 = dfa1.d
# Operating with second regex
print('Это разбор второго регулярного выражения в к-с грамматике : \n')
lengthOfQ = len(dfa1.Q)
myList2 = dfa2.write(lengthOfQ)
#for i in range(len(myList2)):
#    print (myList2[i])
fGLOBAL2 = dfa2.F
diction2 = dfa2.d
first = first_method(myList,myList2)
second = second_method(first)
print('Результат в контекстно-свободной грамматике :')
#print(second)
normal_print(second)
print('Конечный результат :')
print('ab(b|c*)')
input("Нажмите для выхода ...")

#second_method(first)
# Result messages
#print('\nTesting first for : "' + message + '" : ')
#dfa1.run(message)

#print('\nTesting second for : "' + message + '" : ')
#dfa2.run(message)

