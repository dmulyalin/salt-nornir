proxy:
  multiprocessing: true
  proxytype: nornir
  runner:
     plugin: RetryRunner
     options:
        num_workers: 100 
        num_connectors: 100
        connect_retry: 1
        connect_backoff: 1000
        connect_splay: 100
        task_retry: 1
        task_backoff: 1000
        task_splay: 100
        reconnect_on_fail: True
        task_timeout: 600
        
hosts:
  fceos1:
    hostname: 10.0.1.10
    port: 6001
    groups:
    - eos_params
    data:
      device_info:
        model: cEOS_1234
        version: "foobar.17rx.42"
  fceos2:
    hostname: 10.0.1.10
    port: 6002
    groups:
    - eos_params
    data:
      device_info:
        model: cEOS_1234
        version: "foobar.18tx.100"
  fceos3_1:
    hostname: 10.0.1.10
    port: 5001
    groups:
    - eos_params
  fceos3_2:
    hostname: 10.0.1.10
    port: 5002
    groups:
    - eos_params
  fceos3_3:
    hostname: 10.0.1.10
    port: 5003
    groups:
    - eos_params
  fceos3_4:
    hostname: 10.0.1.10
    port: 5004
    groups:
    - eos_params
  fceos3_5:
    hostname: 10.0.1.10
    port: 5005
    groups:
    - eos_params
  fceos3_6:
    hostname: 10.0.1.10
    port: 5006
    groups:
    - eos_params
  fceos3_7:
    hostname: 10.0.1.10
    port: 5007
    groups:
    - eos_params
  fceos3_8:
    hostname: 10.0.1.10
    port: 5008
    groups:
    - eos_params
  fceos3_9:
    hostname: 10.0.1.10
    port: 5009
    groups:
    - eos_params
  fceos3_10:
    hostname: 10.0.1.10
    port: 5010
    groups:
    - eos_params
  fceos3_11:
    hostname: 10.0.1.10
    port: 5011
    groups:
    - eos_params
  fceos3_12:
    hostname: 10.0.1.10
    port: 5012
    groups:
    - eos_params
  fceos3_13:
    hostname: 10.0.1.10
    port: 5013
    groups:
    - eos_params
  fceos3_14:
    hostname: 10.0.1.10
    port: 5014
    groups:
    - eos_params
  fceos3_15:
    hostname: 10.0.1.10
    port: 5015
    groups:
    - eos_params
  fceos3_16:
    hostname: 10.0.1.10
    port: 5016
    groups:
    - eos_params
  fceos3_17:
    hostname: 10.0.1.10
    port: 5017
    groups:
    - eos_params
  fceos3_18:
    hostname: 10.0.1.10
    port: 5018
    groups:
    - eos_params
  fceos3_19:
    hostname: 10.0.1.10
    port: 5019
    groups:
    - eos_params
  fceos3_20:
    hostname: 10.0.1.10
    port: 5020
    groups:
    - eos_params
  fceos3_21:
    hostname: 10.0.1.10
    port: 5021
    groups:
    - eos_params
  fceos3_22:
    hostname: 10.0.1.10
    port: 5022
    groups:
    - eos_params
  fceos3_23:
    hostname: 10.0.1.10
    port: 5023
    groups:
    - eos_params
  fceos3_24:
    hostname: 10.0.1.10
    port: 5024
    groups:
    - eos_params
  fceos3_25:
    hostname: 10.0.1.10
    port: 5025
    groups:
    - eos_params
  fceos3_26:
    hostname: 10.0.1.10
    port: 5026
    groups:
    - eos_params
  fceos3_27:
    hostname: 10.0.1.10
    port: 5027
    groups:
    - eos_params
  fceos3_28:
    hostname: 10.0.1.10
    port: 5028
    groups:
    - eos_params
  fceos3_29:
    hostname: 10.0.1.10
    port: 5029
    groups:
    - eos_params
  fceos3_30:
    hostname: 10.0.1.10
    port: 5030
    groups:
    - eos_params
  fceos3_31:
    hostname: 10.0.1.10
    port: 5031
    groups:
    - eos_params
  fceos3_32:
    hostname: 10.0.1.10
    port: 5032
    groups:
    - eos_params
  fceos3_33:
    hostname: 10.0.1.10
    port: 5033
    groups:
    - eos_params
  fceos3_34:
    hostname: 10.0.1.10
    port: 5034
    groups:
    - eos_params
  fceos3_35:
    hostname: 10.0.1.10
    port: 5035
    groups:
    - eos_params
  fceos3_36:
    hostname: 10.0.1.10
    port: 5036
    groups:
    - eos_params
  fceos3_37:
    hostname: 10.0.1.10
    port: 5037
    groups:
    - eos_params
  fceos3_38:
    hostname: 10.0.1.10
    port: 5038
    groups:
    - eos_params
  fceos3_39:
    hostname: 10.0.1.10
    port: 5039
    groups:
    - eos_params
  fceos3_40:
    hostname: 10.0.1.10
    port: 5040
    groups:
    - eos_params
  fceos3_41:
    hostname: 10.0.1.10
    port: 5041
    groups:
    - eos_params
  fceos3_42:
    hostname: 10.0.1.10
    port: 5042
    groups:
    - eos_params
  fceos3_43:
    hostname: 10.0.1.10
    port: 5043
    groups:
    - eos_params
  fceos3_44:
    hostname: 10.0.1.10
    port: 5044
    groups:
    - eos_params
  fceos3_45:
    hostname: 10.0.1.10
    port: 5045
    groups:
    - eos_params
  fceos3_46:
    hostname: 10.0.1.10
    port: 5046
    groups:
    - eos_params
  fceos3_47:
    hostname: 10.0.1.10
    port: 5047
    groups:
    - eos_params
  fceos3_48:
    hostname: 10.0.1.10
    port: 5048
    groups:
    - eos_params
  fceos3_49:
    hostname: 10.0.1.10
    port: 5049
    groups:
    - eos_params
  fceos3_50:
    hostname: 10.0.1.10
    port: 5050
    groups:
    - eos_params
  fceos3_51:
    hostname: 10.0.1.10
    port: 5051
    groups:
    - eos_params
  fceos3_52:
    hostname: 10.0.1.10
    port: 5052
    groups:
    - eos_params
  fceos3_53:
    hostname: 10.0.1.10
    port: 5053
    groups:
    - eos_params
  fceos3_54:
    hostname: 10.0.1.10
    port: 5054
    groups:
    - eos_params
  fceos3_55:
    hostname: 10.0.1.10
    port: 5055
    groups:
    - eos_params
  fceos3_56:
    hostname: 10.0.1.10
    port: 5056
    groups:
    - eos_params
  fceos3_57:
    hostname: 10.0.1.10
    port: 5057
    groups:
    - eos_params
  fceos3_58:
    hostname: 10.0.1.10
    port: 5058
    groups:
    - eos_params
  fceos3_59:
    hostname: 10.0.1.10
    port: 5059
    groups:
    - eos_params
  fceos3_60:
    hostname: 10.0.1.10
    port: 5060
    groups:
    - eos_params
  fceos3_61:
    hostname: 10.0.1.10
    port: 5061
    groups:
    - eos_params
  fceos3_62:
    hostname: 10.0.1.10
    port: 5062
    groups:
    - eos_params
  fceos3_63:
    hostname: 10.0.1.10
    port: 5063
    groups:
    - eos_params
  fceos3_64:
    hostname: 10.0.1.10
    port: 5064
    groups:
    - eos_params
  fceos3_65:
    hostname: 10.0.1.10
    port: 5065
    groups:
    - eos_params
  fceos3_66:
    hostname: 10.0.1.10
    port: 5066
    groups:
    - eos_params
  fceos3_67:
    hostname: 10.0.1.10
    port: 5067
    groups:
    - eos_params
  fceos3_68:
    hostname: 10.0.1.10
    port: 5068
    groups:
    - eos_params
  fceos3_69:
    hostname: 10.0.1.10
    port: 5069
    groups:
    - eos_params
  fceos3_70:
    hostname: 10.0.1.10
    port: 5070
    groups:
    - eos_params
  fceos3_71:
    hostname: 10.0.1.10
    port: 5071
    groups:
    - eos_params
  fceos3_72:
    hostname: 10.0.1.10
    port: 5072
    groups:
    - eos_params
  fceos3_73:
    hostname: 10.0.1.10
    port: 5073
    groups:
    - eos_params
  fceos3_74:
    hostname: 10.0.1.10
    port: 5074
    groups:
    - eos_params
  fceos3_75:
    hostname: 10.0.1.10
    port: 5075
    groups:
    - eos_params
  fceos3_76:
    hostname: 10.0.1.10
    port: 5076
    groups:
    - eos_params
  fceos3_77:
    hostname: 10.0.1.10
    port: 5077
    groups:
    - eos_params
  fceos3_78:
    hostname: 10.0.1.10
    port: 5078
    groups:
    - eos_params
  fceos3_79:
    hostname: 10.0.1.10
    port: 5079
    groups:
    - eos_params
  fceos3_80:
    hostname: 10.0.1.10
    port: 5080
    groups:
    - eos_params
  fceos3_81:
    hostname: 10.0.1.10
    port: 5081
    groups:
    - eos_params
  fceos3_82:
    hostname: 10.0.1.10
    port: 5082
    groups:
    - eos_params
  fceos3_83:
    hostname: 10.0.1.10
    port: 5083
    groups:
    - eos_params
  fceos3_84:
    hostname: 10.0.1.10
    port: 5084
    groups:
    - eos_params
  fceos3_85:
    hostname: 10.0.1.10
    port: 5085
    groups:
    - eos_params
  fceos3_86:
    hostname: 10.0.1.10
    port: 5086
    groups:
    - eos_params
  fceos3_87:
    hostname: 10.0.1.10
    port: 5087
    groups:
    - eos_params
  fceos3_88:
    hostname: 10.0.1.10
    port: 5088
    groups:
    - eos_params
  fceos3_89:
    hostname: 10.0.1.10
    port: 5089
    groups:
    - eos_params
  fceos3_90:
    hostname: 10.0.1.10
    port: 5090
    groups:
    - eos_params
  fceos3_91:
    hostname: 10.0.1.10
    port: 5091
    groups:
    - eos_params
  fceos3_92:
    hostname: 10.0.1.10
    port: 5092
    groups:
    - eos_params
  fceos3_93:
    hostname: 10.0.1.10
    port: 5093
    groups:
    - eos_params
  fceos3_94:
    hostname: 10.0.1.10
    port: 5094
    groups:
    - eos_params
  fceos3_95:
    hostname: 10.0.1.10
    port: 5095
    groups:
    - eos_params
  fceos3_96:
    hostname: 10.0.1.10
    port: 5096
    groups:
    - eos_params
  fceos3_97:
    hostname: 10.0.1.10
    port: 5097
    groups:
    - eos_params
  fceos3_98:
    hostname: 10.0.1.10
    port: 5098
    groups:
    - eos_params
  fceos3_99:
    hostname: 10.0.1.10
    port: 5099
    groups:
    - eos_params
  fceos3_100:
    hostname: 10.0.1.10
    port: 5100
    groups:
    - eos_params
  fceos3_101:
    hostname: 10.0.1.10
    port: 5101
    groups:
    - eos_params
  fceos3_102:
    hostname: 10.0.1.10
    port: 5102
    groups:
    - eos_params
  fceos3_103:
    hostname: 10.0.1.10
    port: 5103
    groups:
    - eos_params
  fceos3_104:
    hostname: 10.0.1.10
    port: 5104
    groups:
    - eos_params
  fceos3_105:
    hostname: 10.0.1.10
    port: 5105
    groups:
    - eos_params
  fceos3_106:
    hostname: 10.0.1.10
    port: 5106
    groups:
    - eos_params
  fceos3_107:
    hostname: 10.0.1.10
    port: 5107
    groups:
    - eos_params
  fceos3_108:
    hostname: 10.0.1.10
    port: 5108
    groups:
    - eos_params
  fceos3_109:
    hostname: 10.0.1.10
    port: 5109
    groups:
    - eos_params
  fceos3_110:
    hostname: 10.0.1.10
    port: 5110
    groups:
    - eos_params
  fceos3_111:
    hostname: 10.0.1.10
    port: 5111
    groups:
    - eos_params
  fceos3_112:
    hostname: 10.0.1.10
    port: 5112
    groups:
    - eos_params
  fceos3_113:
    hostname: 10.0.1.10
    port: 5113
    groups:
    - eos_params
  fceos3_114:
    hostname: 10.0.1.10
    port: 5114
    groups:
    - eos_params
  fceos3_115:
    hostname: 10.0.1.10
    port: 5115
    groups:
    - eos_params
  fceos3_116:
    hostname: 10.0.1.10
    port: 5116
    groups:
    - eos_params
  fceos3_117:
    hostname: 10.0.1.10
    port: 5117
    groups:
    - eos_params
  fceos3_118:
    hostname: 10.0.1.10
    port: 5118
    groups:
    - eos_params
  fceos3_119:
    hostname: 10.0.1.10
    port: 5119
    groups:
    - eos_params
  fceos3_120:
    hostname: 10.0.1.10
    port: 5120
    groups:
    - eos_params
  fceos3_121:
    hostname: 10.0.1.10
    port: 5121
    groups:
    - eos_params
  fceos3_122:
    hostname: 10.0.1.10
    port: 5122
    groups:
    - eos_params
  fceos3_123:
    hostname: 10.0.1.10
    port: 5123
    groups:
    - eos_params
  fceos3_124:
    hostname: 10.0.1.10
    port: 5124
    groups:
    - eos_params
  fceos3_125:
    hostname: 10.0.1.10
    port: 5125
    groups:
    - eos_params
  fceos3_126:
    hostname: 10.0.1.10
    port: 5126
    groups:
    - eos_params
  fceos3_127:
    hostname: 10.0.1.10
    port: 5127
    groups:
    - eos_params
  fceos3_128:
    hostname: 10.0.1.10
    port: 5128
    groups:
    - eos_params
  fceos3_129:
    hostname: 10.0.1.10
    port: 5129
    groups:
    - eos_params
  fceos3_130:
    hostname: 10.0.1.10
    port: 5130
    groups:
    - eos_params
  fceos3_131:
    hostname: 10.0.1.10
    port: 5131
    groups:
    - eos_params
  fceos3_132:
    hostname: 10.0.1.10
    port: 5132
    groups:
    - eos_params
  fceos3_133:
    hostname: 10.0.1.10
    port: 5133
    groups:
    - eos_params
  fceos3_134:
    hostname: 10.0.1.10
    port: 5134
    groups:
    - eos_params
  fceos3_135:
    hostname: 10.0.1.10
    port: 5135
    groups:
    - eos_params
  fceos3_136:
    hostname: 10.0.1.10
    port: 5136
    groups:
    - eos_params
  fceos3_137:
    hostname: 10.0.1.10
    port: 5137
    groups:
    - eos_params
  fceos3_138:
    hostname: 10.0.1.10
    port: 5138
    groups:
    - eos_params
  fceos3_139:
    hostname: 10.0.1.10
    port: 5139
    groups:
    - eos_params
  fceos3_140:
    hostname: 10.0.1.10
    port: 5140
    groups:
    - eos_params
  fceos3_141:
    hostname: 10.0.1.10
    port: 5141
    groups:
    - eos_params
  fceos3_142:
    hostname: 10.0.1.10
    port: 5142
    groups:
    - eos_params
  fceos3_143:
    hostname: 10.0.1.10
    port: 5143
    groups:
    - eos_params
  fceos3_144:
    hostname: 10.0.1.10
    port: 5144
    groups:
    - eos_params
  fceos3_145:
    hostname: 10.0.1.10
    port: 5145
    groups:
    - eos_params
  fceos3_146:
    hostname: 10.0.1.10
    port: 5146
    groups:
    - eos_params
  fceos3_147:
    hostname: 10.0.1.10
    port: 5147
    groups:
    - eos_params
  fceos3_148:
    hostname: 10.0.1.10
    port: 5148
    groups:
    - eos_params
  fceos3_149:
    hostname: 10.0.1.10
    port: 5149
    groups:
    - eos_params
  fceos3_150:
    hostname: 10.0.1.10
    port: 5150
    groups:
    - eos_params
  fceos3_151:
    hostname: 10.0.1.10
    port: 5151
    groups:
    - eos_params
  fceos3_152:
    hostname: 10.0.1.10
    port: 5152
    groups:
    - eos_params
  fceos3_153:
    hostname: 10.0.1.10
    port: 5153
    groups:
    - eos_params
  fceos3_154:
    hostname: 10.0.1.10
    port: 5154
    groups:
    - eos_params
  fceos3_155:
    hostname: 10.0.1.10
    port: 5155
    groups:
    - eos_params
  fceos3_156:
    hostname: 10.0.1.10
    port: 5156
    groups:
    - eos_params
  fceos3_157:
    hostname: 10.0.1.10
    port: 5157
    groups:
    - eos_params
  fceos3_158:
    hostname: 10.0.1.10
    port: 5158
    groups:
    - eos_params
  fceos3_159:
    hostname: 10.0.1.10
    port: 5159
    groups:
    - eos_params
  fceos3_160:
    hostname: 10.0.1.10
    port: 5160
    groups:
    - eos_params
  fceos3_161:
    hostname: 10.0.1.10
    port: 5161
    groups:
    - eos_params
  fceos3_162:
    hostname: 10.0.1.10
    port: 5162
    groups:
    - eos_params
  fceos3_163:
    hostname: 10.0.1.10
    port: 5163
    groups:
    - eos_params
  fceos3_164:
    hostname: 10.0.1.10
    port: 5164
    groups:
    - eos_params
  fceos3_165:
    hostname: 10.0.1.10
    port: 5165
    groups:
    - eos_params
  fceos3_166:
    hostname: 10.0.1.10
    port: 5166
    groups:
    - eos_params
  fceos3_167:
    hostname: 10.0.1.10
    port: 5167
    groups:
    - eos_params
  fceos3_168:
    hostname: 10.0.1.10
    port: 5168
    groups:
    - eos_params
  fceos3_169:
    hostname: 10.0.1.10
    port: 5169
    groups:
    - eos_params
  fceos3_170:
    hostname: 10.0.1.10
    port: 5170
    groups:
    - eos_params
  fceos3_171:
    hostname: 10.0.1.10
    port: 5171
    groups:
    - eos_params
  fceos3_172:
    hostname: 10.0.1.10
    port: 5172
    groups:
    - eos_params
  fceos3_173:
    hostname: 10.0.1.10
    port: 5173
    groups:
    - eos_params
  fceos3_174:
    hostname: 10.0.1.10
    port: 5174
    groups:
    - eos_params
  fceos3_175:
    hostname: 10.0.1.10
    port: 5175
    groups:
    - eos_params
  fceos3_176:
    hostname: 10.0.1.10
    port: 5176
    groups:
    - eos_params
  fceos3_177:
    hostname: 10.0.1.10
    port: 5177
    groups:
    - eos_params
  fceos3_178:
    hostname: 10.0.1.10
    port: 5178
    groups:
    - eos_params
  fceos3_179:
    hostname: 10.0.1.10
    port: 5179
    groups:
    - eos_params
  fceos3_180:
    hostname: 10.0.1.10
    port: 5180
    groups:
    - eos_params
  fceos3_181:
    hostname: 10.0.1.10
    port: 5181
    groups:
    - eos_params
  fceos3_182:
    hostname: 10.0.1.10
    port: 5182
    groups:
    - eos_params
  fceos3_183:
    hostname: 10.0.1.10
    port: 5183
    groups:
    - eos_params
  fceos3_184:
    hostname: 10.0.1.10
    port: 5184
    groups:
    - eos_params
  fceos3_185:
    hostname: 10.0.1.10
    port: 5185
    groups:
    - eos_params
  fceos3_186:
    hostname: 10.0.1.10
    port: 5186
    groups:
    - eos_params
  fceos3_187:
    hostname: 10.0.1.10
    port: 5187
    groups:
    - eos_params
  fceos3_188:
    hostname: 10.0.1.10
    port: 5188
    groups:
    - eos_params
  fceos3_189:
    hostname: 10.0.1.10
    port: 5189
    groups:
    - eos_params
  fceos3_190:
    hostname: 10.0.1.10
    port: 5190
    groups:
    - eos_params
  fceos3_191:
    hostname: 10.0.1.10
    port: 5191
    groups:
    - eos_params
  fceos3_192:
    hostname: 10.0.1.10
    port: 5192
    groups:
    - eos_params
  fceos3_193:
    hostname: 10.0.1.10
    port: 5193
    groups:
    - eos_params
  fceos3_194:
    hostname: 10.0.1.10
    port: 5194
    groups:
    - eos_params
  fceos3_195:
    hostname: 10.0.1.10
    port: 5195
    groups:
    - eos_params
  fceos3_196:
    hostname: 10.0.1.10
    port: 5196
    groups:
    - eos_params
  fceos3_197:
    hostname: 10.0.1.10
    port: 5197
    groups:
    - eos_params
  fceos3_198:
    hostname: 10.0.1.10
    port: 5198
    groups:
    - eos_params
  fceos3_199:
    hostname: 10.0.1.10
    port: 5199
    groups:
    - eos_params
  fceos3_200:
    hostname: 10.0.1.10
    port: 5200
    groups:
    - eos_params
  fceos3_201:
    hostname: 10.0.1.10
    port: 5201
    groups:
    - eos_params
  fceos3_202:
    hostname: 10.0.1.10
    port: 5202
    groups:
    - eos_params
  fceos3_203:
    hostname: 10.0.1.10
    port: 5203
    groups:
    - eos_params
  fceos3_204:
    hostname: 10.0.1.10
    port: 5204
    groups:
    - eos_params
  fceos3_205:
    hostname: 10.0.1.10
    port: 5205
    groups:
    - eos_params
  fceos3_206:
    hostname: 10.0.1.10
    port: 5206
    groups:
    - eos_params
  fceos3_207:
    hostname: 10.0.1.10
    port: 5207
    groups:
    - eos_params
  fceos3_208:
    hostname: 10.0.1.10
    port: 5208
    groups:
    - eos_params
  fceos3_209:
    hostname: 10.0.1.10
    port: 5209
    groups:
    - eos_params
  fceos3_210:
    hostname: 10.0.1.10
    port: 5210
    groups:
    - eos_params
  fceos3_211:
    hostname: 10.0.1.10
    port: 5211
    groups:
    - eos_params
  fceos3_212:
    hostname: 10.0.1.10
    port: 5212
    groups:
    - eos_params
  fceos3_213:
    hostname: 10.0.1.10
    port: 5213
    groups:
    - eos_params
  fceos3_214:
    hostname: 10.0.1.10
    port: 5214
    groups:
    - eos_params
  fceos3_215:
    hostname: 10.0.1.10
    port: 5215
    groups:
    - eos_params
  fceos3_216:
    hostname: 10.0.1.10
    port: 5216
    groups:
    - eos_params
  fceos3_217:
    hostname: 10.0.1.10
    port: 5217
    groups:
    - eos_params
  fceos3_218:
    hostname: 10.0.1.10
    port: 5218
    groups:
    - eos_params
  fceos3_219:
    hostname: 10.0.1.10
    port: 5219
    groups:
    - eos_params
  fceos3_220:
    hostname: 10.0.1.10
    port: 5220
    groups:
    - eos_params
  fceos3_221:
    hostname: 10.0.1.10
    port: 5221
    groups:
    - eos_params
  fceos3_222:
    hostname: 10.0.1.10
    port: 5222
    groups:
    - eos_params
  fceos3_223:
    hostname: 10.0.1.10
    port: 5223
    groups:
    - eos_params
  fceos3_224:
    hostname: 10.0.1.10
    port: 5224
    groups:
    - eos_params
  fceos3_225:
    hostname: 10.0.1.10
    port: 5225
    groups:
    - eos_params
  fceos3_226:
    hostname: 10.0.1.10
    port: 5226
    groups:
    - eos_params
  fceos3_227:
    hostname: 10.0.1.10
    port: 5227
    groups:
    - eos_params
  fceos3_228:
    hostname: 10.0.1.10
    port: 5228
    groups:
    - eos_params
  fceos3_229:
    hostname: 10.0.1.10
    port: 5229
    groups:
    - eos_params
  fceos3_230:
    hostname: 10.0.1.10
    port: 5230
    groups:
    - eos_params
  fceos3_231:
    hostname: 10.0.1.10
    port: 5231
    groups:
    - eos_params
  fceos3_232:
    hostname: 10.0.1.10
    port: 5232
    groups:
    - eos_params
  fceos3_233:
    hostname: 10.0.1.10
    port: 5233
    groups:
    - eos_params
  fceos3_234:
    hostname: 10.0.1.10
    port: 5234
    groups:
    - eos_params
  fceos3_235:
    hostname: 10.0.1.10
    port: 5235
    groups:
    - eos_params
  fceos3_236:
    hostname: 10.0.1.10
    port: 5236
    groups:
    - eos_params
  fceos3_237:
    hostname: 10.0.1.10
    port: 5237
    groups:
    - eos_params
  fceos3_238:
    hostname: 10.0.1.10
    port: 5238
    groups:
    - eos_params
  fceos3_239:
    hostname: 10.0.1.10
    port: 5239
    groups:
    - eos_params
  fceos3_240:
    hostname: 10.0.1.10
    port: 5240
    groups:
    - eos_params
  fceos3_241:
    hostname: 10.0.1.10
    port: 5241
    groups:
    - eos_params
  fceos3_242:
    hostname: 10.0.1.10
    port: 5242
    groups:
    - eos_params
  fceos3_243:
    hostname: 10.0.1.10
    port: 5243
    groups:
    - eos_params
  fceos3_244:
    hostname: 10.0.1.10
    port: 5244
    groups:
    - eos_params
  fceos3_245:
    hostname: 10.0.1.10
    port: 5245
    groups:
    - eos_params
  fceos3_246:
    hostname: 10.0.1.10
    port: 5246
    groups:
    - eos_params
  fceos3_247:
    hostname: 10.0.1.10
    port: 5247
    groups:
    - eos_params
  fceos3_248:
    hostname: 10.0.1.10
    port: 5248
    groups:
    - eos_params
  fceos3_249:
    hostname: 10.0.1.10
    port: 5249
    groups:
    - eos_params
  fceos3_250:
    hostname: 10.0.1.10
    port: 5250
    groups:
    - eos_params
  fceos3_251:
    hostname: 10.0.1.10
    port: 5251
    groups:
    - eos_params
  fceos3_252:
    hostname: 10.0.1.10
    port: 5252
    groups:
    - eos_params
  fceos3_253:
    hostname: 10.0.1.10
    port: 5253
    groups:
    - eos_params
  fceos3_254:
    hostname: 10.0.1.10
    port: 5254
    groups:
    - eos_params
  fceos3_255:
    hostname: 10.0.1.10
    port: 5255
    groups:
    - eos_params
  fceos3_256:
    hostname: 10.0.1.10
    port: 5256
    groups:
    - eos_params
  fceos3_257:
    hostname: 10.0.1.10
    port: 5257
    groups:
    - eos_params
  fceos3_258:
    hostname: 10.0.1.10
    port: 5258
    groups:
    - eos_params
  fceos3_259:
    hostname: 10.0.1.10
    port: 5259
    groups:
    - eos_params
  fceos3_260:
    hostname: 10.0.1.10
    port: 5260
    groups:
    - eos_params
  fceos3_261:
    hostname: 10.0.1.10
    port: 5261
    groups:
    - eos_params
  fceos3_262:
    hostname: 10.0.1.10
    port: 5262
    groups:
    - eos_params
  fceos3_263:
    hostname: 10.0.1.10
    port: 5263
    groups:
    - eos_params
  fceos3_264:
    hostname: 10.0.1.10
    port: 5264
    groups:
    - eos_params
  fceos3_265:
    hostname: 10.0.1.10
    port: 5265
    groups:
    - eos_params
  fceos3_266:
    hostname: 10.0.1.10
    port: 5266
    groups:
    - eos_params
  fceos3_267:
    hostname: 10.0.1.10
    port: 5267
    groups:
    - eos_params
  fceos3_268:
    hostname: 10.0.1.10
    port: 5268
    groups:
    - eos_params
  fceos3_269:
    hostname: 10.0.1.10
    port: 5269
    groups:
    - eos_params
  fceos3_270:
    hostname: 10.0.1.10
    port: 5270
    groups:
    - eos_params
  fceos3_271:
    hostname: 10.0.1.10
    port: 5271
    groups:
    - eos_params
  fceos3_272:
    hostname: 10.0.1.10
    port: 5272
    groups:
    - eos_params
  fceos3_273:
    hostname: 10.0.1.10
    port: 5273
    groups:
    - eos_params
  fceos3_274:
    hostname: 10.0.1.10
    port: 5274
    groups:
    - eos_params
  fceos3_275:
    hostname: 10.0.1.10
    port: 5275
    groups:
    - eos_params
  fceos3_276:
    hostname: 10.0.1.10
    port: 5276
    groups:
    - eos_params
  fceos3_277:
    hostname: 10.0.1.10
    port: 5277
    groups:
    - eos_params
  fceos3_278:
    hostname: 10.0.1.10
    port: 5278
    groups:
    - eos_params
  fceos3_279:
    hostname: 10.0.1.10
    port: 5279
    groups:
    - eos_params
  fceos3_280:
    hostname: 10.0.1.10
    port: 5280
    groups:
    - eos_params
  fceos3_281:
    hostname: 10.0.1.10
    port: 5281
    groups:
    - eos_params
  fceos3_282:
    hostname: 10.0.1.10
    port: 5282
    groups:
    - eos_params
  fceos3_283:
    hostname: 10.0.1.10
    port: 5283
    groups:
    - eos_params
  fceos3_284:
    hostname: 10.0.1.10
    port: 5284
    groups:
    - eos_params
  fceos3_285:
    hostname: 10.0.1.10
    port: 5285
    groups:
    - eos_params
  fceos3_286:
    hostname: 10.0.1.10
    port: 5286
    groups:
    - eos_params
  fceos3_287:
    hostname: 10.0.1.10
    port: 5287
    groups:
    - eos_params
  fceos3_288:
    hostname: 10.0.1.10
    port: 5288
    groups:
    - eos_params
  fceos3_289:
    hostname: 10.0.1.10
    port: 5289
    groups:
    - eos_params
  fceos3_290:
    hostname: 10.0.1.10
    port: 5290
    groups:
    - eos_params
  fceos3_291:
    hostname: 10.0.1.10
    port: 5291
    groups:
    - eos_params
  fceos3_292:
    hostname: 10.0.1.10
    port: 5292
    groups:
    - eos_params
  fceos3_293:
    hostname: 10.0.1.10
    port: 5293
    groups:
    - eos_params
  fceos3_294:
    hostname: 10.0.1.10
    port: 5294
    groups:
    - eos_params
  fceos3_295:
    hostname: 10.0.1.10
    port: 5295
    groups:
    - eos_params
  fceos3_296:
    hostname: 10.0.1.10
    port: 5296
    groups:
    - eos_params
  fceos3_297:
    hostname: 10.0.1.10
    port: 5297
    groups:
    - eos_params
  fceos3_298:
    hostname: 10.0.1.10
    port: 5298
    groups:
    - eos_params
  fceos3_299:
    hostname: 10.0.1.10
    port: 5299
    groups:
    - eos_params
  fceos3_300:
    hostname: 10.0.1.10
    port: 5300
    groups:
    - eos_params
  fceos3_301:
    hostname: 10.0.1.10
    port: 5301
    groups:
    - eos_params
  fceos3_302:
    hostname: 10.0.1.10
    port: 5302
    groups:
    - eos_params
  fceos3_303:
    hostname: 10.0.1.10
    port: 5303
    groups:
    - eos_params
  fceos3_304:
    hostname: 10.0.1.10
    port: 5304
    groups:
    - eos_params
  fceos3_305:
    hostname: 10.0.1.10
    port: 5305
    groups:
    - eos_params
  fceos3_306:
    hostname: 10.0.1.10
    port: 5306
    groups:
    - eos_params
  fceos3_307:
    hostname: 10.0.1.10
    port: 5307
    groups:
    - eos_params
  fceos3_308:
    hostname: 10.0.1.10
    port: 5308
    groups:
    - eos_params
  fceos3_309:
    hostname: 10.0.1.10
    port: 5309
    groups:
    - eos_params
  fceos3_310:
    hostname: 10.0.1.10
    port: 5310
    groups:
    - eos_params
  fceos3_311:
    hostname: 10.0.1.10
    port: 5311
    groups:
    - eos_params
  fceos3_312:
    hostname: 10.0.1.10
    port: 5312
    groups:
    - eos_params
  fceos3_313:
    hostname: 10.0.1.10
    port: 5313
    groups:
    - eos_params
  fceos3_314:
    hostname: 10.0.1.10
    port: 5314
    groups:
    - eos_params
  fceos3_315:
    hostname: 10.0.1.10
    port: 5315
    groups:
    - eos_params
  fceos3_316:
    hostname: 10.0.1.10
    port: 5316
    groups:
    - eos_params
  fceos3_317:
    hostname: 10.0.1.10
    port: 5317
    groups:
    - eos_params
  fceos3_318:
    hostname: 10.0.1.10
    port: 5318
    groups:
    - eos_params
  fceos3_319:
    hostname: 10.0.1.10
    port: 5319
    groups:
    - eos_params
  fceos3_320:
    hostname: 10.0.1.10
    port: 5320
    groups:
    - eos_params
  fceos3_321:
    hostname: 10.0.1.10
    port: 5321
    groups:
    - eos_params
  fceos3_322:
    hostname: 10.0.1.10
    port: 5322
    groups:
    - eos_params
  fceos3_323:
    hostname: 10.0.1.10
    port: 5323
    groups:
    - eos_params
  fceos3_324:
    hostname: 10.0.1.10
    port: 5324
    groups:
    - eos_params
  fceos3_325:
    hostname: 10.0.1.10
    port: 5325
    groups:
    - eos_params
  fceos3_326:
    hostname: 10.0.1.10
    port: 5326
    groups:
    - eos_params
  fceos3_327:
    hostname: 10.0.1.10
    port: 5327
    groups:
    - eos_params
  fceos3_328:
    hostname: 10.0.1.10
    port: 5328
    groups:
    - eos_params
  fceos3_329:
    hostname: 10.0.1.10
    port: 5329
    groups:
    - eos_params
  fceos3_330:
    hostname: 10.0.1.10
    port: 5330
    groups:
    - eos_params
  fceos3_331:
    hostname: 10.0.1.10
    port: 5331
    groups:
    - eos_params
  fceos3_332:
    hostname: 10.0.1.10
    port: 5332
    groups:
    - eos_params
  fceos3_333:
    hostname: 10.0.1.10
    port: 5333
    groups:
    - eos_params
  fceos3_334:
    hostname: 10.0.1.10
    port: 5334
    groups:
    - eos_params
  fceos3_335:
    hostname: 10.0.1.10
    port: 5335
    groups:
    - eos_params
  fceos3_336:
    hostname: 10.0.1.10
    port: 5336
    groups:
    - eos_params
  fceos3_337:
    hostname: 10.0.1.10
    port: 5337
    groups:
    - eos_params
  fceos3_338:
    hostname: 10.0.1.10
    port: 5338
    groups:
    - eos_params
  fceos3_339:
    hostname: 10.0.1.10
    port: 5339
    groups:
    - eos_params
  fceos3_340:
    hostname: 10.0.1.10
    port: 5340
    groups:
    - eos_params
  fceos3_341:
    hostname: 10.0.1.10
    port: 5341
    groups:
    - eos_params
  fceos3_342:
    hostname: 10.0.1.10
    port: 5342
    groups:
    - eos_params
  fceos3_343:
    hostname: 10.0.1.10
    port: 5343
    groups:
    - eos_params
  fceos3_344:
    hostname: 10.0.1.10
    port: 5344
    groups:
    - eos_params
  fceos3_345:
    hostname: 10.0.1.10
    port: 5345
    groups:
    - eos_params
  fceos3_346:
    hostname: 10.0.1.10
    port: 5346
    groups:
    - eos_params
  fceos3_347:
    hostname: 10.0.1.10
    port: 5347
    groups:
    - eos_params
  fceos3_348:
    hostname: 10.0.1.10
    port: 5348
    groups:
    - eos_params
  fceos3_349:
    hostname: 10.0.1.10
    port: 5349
    groups:
    - eos_params
  fceos3_350:
    hostname: 10.0.1.10
    port: 5350
    groups:
    - eos_params
  fceos3_351:
    hostname: 10.0.1.10
    port: 5351
    groups:
    - eos_params
  fceos3_352:
    hostname: 10.0.1.10
    port: 5352
    groups:
    - eos_params
  fceos3_353:
    hostname: 10.0.1.10
    port: 5353
    groups:
    - eos_params
  fceos3_354:
    hostname: 10.0.1.10
    port: 5354
    groups:
    - eos_params
  fceos3_355:
    hostname: 10.0.1.10
    port: 5355
    groups:
    - eos_params
  fceos3_356:
    hostname: 10.0.1.10
    port: 5356
    groups:
    - eos_params
  fceos3_357:
    hostname: 10.0.1.10
    port: 5357
    groups:
    - eos_params
  fceos3_358:
    hostname: 10.0.1.10
    port: 5358
    groups:
    - eos_params
  fceos3_359:
    hostname: 10.0.1.10
    port: 5359
    groups:
    - eos_params
  fceos3_360:
    hostname: 10.0.1.10
    port: 5360
    groups:
    - eos_params
  fceos3_361:
    hostname: 10.0.1.10
    port: 5361
    groups:
    - eos_params
  fceos3_362:
    hostname: 10.0.1.10
    port: 5362
    groups:
    - eos_params
  fceos3_363:
    hostname: 10.0.1.10
    port: 5363
    groups:
    - eos_params
  fceos3_364:
    hostname: 10.0.1.10
    port: 5364
    groups:
    - eos_params
  fceos3_365:
    hostname: 10.0.1.10
    port: 5365
    groups:
    - eos_params
  fceos3_366:
    hostname: 10.0.1.10
    port: 5366
    groups:
    - eos_params
  fceos3_367:
    hostname: 10.0.1.10
    port: 5367
    groups:
    - eos_params
  fceos3_368:
    hostname: 10.0.1.10
    port: 5368
    groups:
    - eos_params
  fceos3_369:
    hostname: 10.0.1.10
    port: 5369
    groups:
    - eos_params
  fceos3_370:
    hostname: 10.0.1.10
    port: 5370
    groups:
    - eos_params
  fceos3_371:
    hostname: 10.0.1.10
    port: 5371
    groups:
    - eos_params
  fceos3_372:
    hostname: 10.0.1.10
    port: 5372
    groups:
    - eos_params
  fceos3_373:
    hostname: 10.0.1.10
    port: 5373
    groups:
    - eos_params
  fceos3_374:
    hostname: 10.0.1.10
    port: 5374
    groups:
    - eos_params
  fceos3_375:
    hostname: 10.0.1.10
    port: 5375
    groups:
    - eos_params
  fceos3_376:
    hostname: 10.0.1.10
    port: 5376
    groups:
    - eos_params
  fceos3_377:
    hostname: 10.0.1.10
    port: 5377
    groups:
    - eos_params
  fceos3_378:
    hostname: 10.0.1.10
    port: 5378
    groups:
    - eos_params
  fceos3_379:
    hostname: 10.0.1.10
    port: 5379
    groups:
    - eos_params
  fceos3_380:
    hostname: 10.0.1.10
    port: 5380
    groups:
    - eos_params
  fceos3_381:
    hostname: 10.0.1.10
    port: 5381
    groups:
    - eos_params
  fceos3_382:
    hostname: 10.0.1.10
    port: 5382
    groups:
    - eos_params
  fceos3_383:
    hostname: 10.0.1.10
    port: 5383
    groups:
    - eos_params
  fceos3_384:
    hostname: 10.0.1.10
    port: 5384
    groups:
    - eos_params
  fceos3_385:
    hostname: 10.0.1.10
    port: 5385
    groups:
    - eos_params
  fceos3_386:
    hostname: 10.0.1.10
    port: 5386
    groups:
    - eos_params
  fceos3_387:
    hostname: 10.0.1.10
    port: 5387
    groups:
    - eos_params
  fceos3_388:
    hostname: 10.0.1.10
    port: 5388
    groups:
    - eos_params
  fceos3_389:
    hostname: 10.0.1.10
    port: 5389
    groups:
    - eos_params
  fceos3_390:
    hostname: 10.0.1.10
    port: 5390
    groups:
    - eos_params
  fceos3_391:
    hostname: 10.0.1.10
    port: 5391
    groups:
    - eos_params
  fceos3_392:
    hostname: 10.0.1.10
    port: 5392
    groups:
    - eos_params
  fceos3_393:
    hostname: 10.0.1.10
    port: 5393
    groups:
    - eos_params
  fceos3_394:
    hostname: 10.0.1.10
    port: 5394
    groups:
    - eos_params
  fceos3_395:
    hostname: 10.0.1.10
    port: 5395
    groups:
    - eos_params
  fceos3_396:
    hostname: 10.0.1.10
    port: 5396
    groups:
    - eos_params
  fceos3_397:
    hostname: 10.0.1.10
    port: 5397
    groups:
    - eos_params
  fceos3_398:
    hostname: 10.0.1.10
    port: 5398
    groups:
    - eos_params
  fceos3_399:
    hostname: 10.0.1.10
    port: 5399
    groups:
    - eos_params
  fceos3_400:
    hostname: 10.0.1.10
    port: 5400
    groups:
    - eos_params
  iosxr1:
    hostname: 10.0.1.10
    port: 7777
    groups:
    - xr_params
    
groups:
  eos_params:
    connection_options:
      scrapli:
        extras:
          auth_strict_key: false
          ssh_config_file: false
        platform: arista_eos
    password: nornir
    username: nornir
    platform: arista_eos
  xr_params:
    password: nornir
    username: nornir
    platform: cisco_xr   
    
nornir:
  actions: {}

defaults:
  data: 
    device_info:
      model: cEOS_foobar
      version: "foobar.199.42"
      
salt_nornir_netbox_pillar:
  use_minion_id_device: True
  use_minion_id_tag: True
  use_hosts_filters: True
  host_add_netbox_data: netbox
  host_add_interfaces: True
  host_add_interfaces_ip: True
  host_add_connections: True
  hosts_filters: 
    - name__ic: "fceos5"
    - name__ic: "fceos4"
    - name__ic: "__not_exists__"
  secrets:
    resolve_secrets: True
    fetch_username: True
    fetch_password: True
    secret_name_map: 
      bgp_peer_secret: peer_ip
    plugins:
      netbox_secrets:
        private_key: /etc/salt/netbox_secrets_private.key