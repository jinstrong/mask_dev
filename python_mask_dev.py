import os
import re
import math
from tqdm import tqdm

class MaskStil:
    def __init__(self):
        self.log_signal_file = ''
        self.pattern = r"^([^:]+)(:)(\d+)(\s+)(\d+)(\s+)(\d+)(\s+)(\d+)(\s)([.LH]+)$"
        self.log_signal = {}
        self.log_lines = []
        self.mask_dict = {}
        self.stil_name_new = ''
        self.stil_name = ''
        self.signal_all = {}
        self.signal_group = []
        self.offset = 0
        self.mask_mode = -1  # mask_mode 0: revert between L/H; mask_mode 1: mask L/H to Z
        self.convert_value=[{"L":"H", "H":"L"}, {"L":"Z", "H":"Z"}]
        for i in range(100):
            self.log_signal[i] = ''

    def digest(self, log_signal, stil_file, signal_group, offset, mask_mode = 1):
        self.log_signal_file = log_signal
        self.stil_name = stil_file
        self.stil_name_new = stil_file[:-5] + '_mask.stil'
        self.signal_group = signal_group.replace('=', '+').strip().split('+')
        self.offset = offset
        self.mask_mode = mask_mode
        for i in range(1, len(self.signal_group)):
            self.signal_all[self.signal_group[i]] = (i - 1) / 10 + i
        print(self.signal_all)
        self.parse_log()
        self.stil_parse()

    def parse_log(self):
        with open(self.log_signal_file) as infile:
            line_num = 0
            blank_line = 0
            for line in infile:
                line_num += 1
                if line_num == 1:
                    blank_line = line.count(' ')
                if "------------------" in line:
                    break
                for i in range(blank_line, len(line)):
                    self.log_signal[i - blank_line] += line[i]
        for (key, value) in self.log_signal.items():
            self.log_signal[key] = value.rstrip()
        print(self.log_signal)
        with open(self.log_signal_file) as log_in:
            self.log_lines = log_in.read().splitlines()
        for line in self.log_lines:
            if re.match(self.pattern, line):
                match = re.match(self.pattern, line)
                cycle = int(match.group(9))
                signals = match.group(11)
                # print cycle,signals
                self.mask_dict[cycle] = {}
                for i in range(len(signals)):
                    if signals[i] != '.':
                        self.mask_dict[cycle][i] = signals[i]

    def stil_parse(self):

        cycle_keys = []
        vector_num = 0
        for i in self.mask_dict.keys():
            cycle_keys.append(i)
        with open(self.stil_name, 'r') as stil_in:
            stil_in_list = stil_in.read().splitlines()
        total_len = len(stil_in_list)
        vector_cycle_dict = {}
        with tqdm(total=total_len, ncols=100, desc= " Stil Scanning in RAM Progress") as pbar:
            for i_iter in range(total_len):
                line = stil_in_list[i_iter]
                pbar.update(1)        
                if "=" in line:
                    vector_num +=1
                    if (vector_num in cycle_keys):
                        vector_cycle_dict[vector_num] = i_iter


                        status = line[line.find("=") + 1:line.find(";")]
                        # if cycle + self.offset in cycle_keys:
                        if vector_num in cycle_keys:
                            match = 1
                            for (i, j) in self.mask_dict[vector_num].iteritems():
                                mask_point = i

                                mask_signal = self.log_signal[i]
                                mask_value = j
                                test_point = self.signal_all[mask_signal]
                                test_value = status[test_point]
                                if test_value != mask_value:
                                    print("data did not match for cycle: ", test_value, " VS ", line, j, vector_num, mask_point, mask_signal, test_point, test_value)
                                    match = 0
                                    raise NameError
                                else:

                                    status = status[:test_point] + self.convert_value[self.mask_mode][test_value] + status[test_point + 1:]
                            if match == 1:
                                replace_line = line[:line.find("=") + 1] + status + line[line.find(";"):]
                            print("data change from :", line)
                            print("               to:", replace_line)
                            stil_in_list[i_iter] = replace_line
                        else:
                            print("No matching for %d with %s" %(vector_num, line))
                            raise NameError

        with tqdm(total=len(stil_in_list), ncols=100, desc= " Masked-stil to in RAM Progress") as pbar:
            with open(self.stil_name_new, 'w') as stil_out:
                for new_line in range(len(stil_in_list)):
                    pbar.update(1)
                    stil_out.write(new_line)
