from typing import List

FLAG: str = "-"


def flag_arg_name(arg) -> str:
    return f"{FLAG}{arg}"


def preprocess_input(user_input: List[str]):
    words = []
    temp_word = []
    flag = None
    positional_done = False

    for word in user_input:
        if word.startswith('-') and len(word) > 1:
            if temp_word:
                if flag:
                    words.append(flag)
                    words.append(" ".join(temp_word))
                else:
                    words.extend(temp_word)
                temp_word = []
            flag = word
            positional_done = True
        else:
            if positional_done:
                temp_word.append(word)
            else:
                words.append(word)

    if temp_word:
        if flag:
            words.append(flag)
            words.append(" ".join(temp_word))
        else:
            words.extend(temp_word)

    return words
