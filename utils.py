import pandas as pd
import os
import re
import json


def venn_diagram(file1, file2, caller):
    """
        get the venn diagram numbers(uniqueA,common,uniqueB) given the two vcf files

        :param file1: path to filtered vcf file1
        :param file2: path to filtered vcf file2
        :param caller: compare the variants with the selected filter
        :return: common number, uniqueA number, uniqueB number
        :rtype: int
        """

    dfA = pd.read_table(file1, header=None)
    dfB = pd.read_table(file2, header=None)

    # if caller in ['af','dbsnp','ffpe','merge','PASS','proximity']:
    if caller == 'vcf_all':
        dfA_filter = dfA[[0, 1]]
        dfB_filter = dfB[[0, 1]]
    else:
        dfA_filter = dfA[dfA[2] == caller][[0, 1]]
        dfB_filter = dfB[dfB[2] == caller][[0, 1]]
    # else:
    #     dfA_filter = dfA[dfA[2] == 'PASS'][[0, 1]]
    #     dfB_filter = dfB[dfB[2] == 'PASS'][[0, 1]]

    # return common, uniqueA, uniqueB in venn diagram
    return len(pd.merge(dfA_filter, dfB_filter, how='inner')), \
           len(dfA_filter.merge(dfB_filter, indicator=True, how='left').loc[lambda x: x['_merge'] != 'both']), \
           len(dfA_filter.merge(dfB_filter, indicator=True, how='right').loc[lambda x: x['_merge'] != 'both'])


def chart(filelist,vcf_file_type):
    """
        get the distribution of each vcf file in the file list

        :param filelist: filedict that contains all the vcf files
        :param vcf_file_type: which kind of vcf file, ProximityFiltered? mutect_somatic_depth_filter?
        :return: df of the distribution
        :rtype: dataframe
        """
    if vcf_file_type == 'ProximityFiltered':
        out_list = ['dat/' + re.search('[0-9|a-z]{8}-[0-9|a-z]{4}-[0-9|a-z]{4}-[0-9|a-z]{4}-[0-9|a-z]{12}',path).group(0) + '/ProximityFiltered.txt' for path in filelist]
    else:
        out_list = ['dat/' + re.search('[0-9|a-z]{8}-[0-9|a-z]{4}-[0-9|a-z]{4}-[0-9|a-z]{4}-[0-9|a-z]{12}',path).group(0) + '/' + vcf_file_type + '.output.txt' for path in filelist]
    used_filters = get_used_filters(out_list)
    if 'vcf_all' in used_filters:
        used_filters.remove('vcf_all')
    print(used_filters)
    df_res = pd.DataFrame(columns=['cromwell_workflow_id'] + used_filters + ['total'])
    for path in out_list:
        numbers = {}
        cromwell_workflow_id = re.search('[0-9|a-z]{8}-[0-9|a-z]{4}-[0-9|a-z]{4}-[0-9|a-z]{4}-[0-9|a-z]{12}',
                                         path).group(0)
        numbers['cromwell_workflow_id'] = cromwell_workflow_id
        df = pd.read_table(path, header=None)
        total = len(df)
        for filter in used_filters:
            numbers[filter] = len(df[df[2].str.contains(filter)]) / total

        numbers['total'] = total
        df_res = df_res.append(numbers, ignore_index=True)




        # df = pd.read_table(path, header=None)
        # total = len(df)
        # pass_number = len(df[df[2].str.contains('PASS')])
        # af_number = len(df[df[2].str.contains('af')])
        # dbsnp_number = len(df[df[2].str.contains('af')])
        # ffpe_number = len(df[df[2].str.contains('ffpe')])
        # merge_number = len(df[df[2].str.contains('merge')])
        # proximity_number = len(df[df[2].str.contains('proximity')])
        #
        # df_res = df_res.append(
        #     {'cromwell_workflow_id': cromwell_workflow_id, 'PASS': pass_number / total, 'af': af_number / total, 'dbsnp': dbsnp_number / total,
        #      'ffpe': ffpe_number / total, 'merge': merge_number / total,
        #      'proximity': proximity_number / total, 'total': total}, ignore_index=True)
    return df_res


def get_filters_dict(vcf_file1, vcf_file2):
    """
    Read two vcf files to get all the filters and their description

    :param vcf_file2: Path to a vcf file 1.
    :param vcf_file1: Path to a vcf file 2.
    :return: dict of all filters and description
    :rtype: dict
    """
    vcf_dict = []
    with open(vcf_file1, 'r') as invcf:
        for line in invcf:
            if line.startswith('#'):
                if 'FILTER=' in line:
                    vcf_dict.append(re.findall('<([^】]+)>', line)[0])
    vcf_dict = {item.split(',')[0].split('=')[1]: item.split(',')[1].split('=')[1][1:-1] for item in vcf_dict}

    with open(vcf_file2, 'r') as invcf:
        for line in invcf:
            if line.startswith('#'):
                if 'FILTER=' in line:
                    str1 = re.findall('<([^】]+)>', line)[0]
                    if (
                            str1.split(',')[0].split('=')[1],
                            str1.split(',')[1].split('=')[1][1:-1]) not in vcf_dict.items():
                        vcf_dict[str1.split(',')[0].split('=')[1]] = str1.split(',')[1].split('=')[1][1:-1]

    return vcf_dict


def get_used_filters(path_list):
    """
    Read two filterd vcf file(which is a txt file with chr,pos,filter) and return all the filters used in this two vcf files

    :param path_list: Path list of filterd vcf files
    :return: all the filters used in this two vcf files
    :rtype: list
    """
    df_res = pd.DataFrame(columns=[0,1,2])
    filters = []
    for path in path_list:
        df = pd.read_table(path, header=None)
        for item in pd.concat([df_res, df])[2].unique():
            if ';' in item:
                for i in item.split(';'):
                    if i not in filters:
                        filters.append(i)
            else:
                # print(item)
                if item not in filters:
                    filters.append(item)
    return ['vcf_all'] + filters


def data_prepare(filelist):
    """
        prepare the data to be used.

        :param filelist: file list that contains all the vcf files
        :return: None
        :rtype: None
        """
    for path in filelist:
        cromwell_workflow_id = re.search('[0-9|a-z]{8}-[0-9|a-z]{4}-[0-9|a-z]{4}-[0-9|a-z]{4}-[0-9|a-z]{12}',
                                         path).group(0)
        out = 'dat/' + cromwell_workflow_id + '/'
        # create a folder name with its cromwell_workflow_id in dat
        if not os.path.exists(out):
            os.system('mkdir ' + out)
        # check and create txt file for out vcf all
        if os.path.exists(
                path + 'call-snp_indel_proximity_filter/execution/output/ProximityFiltered.vcf') and not os.path.exists(
            out + 'ProximityFiltered.txt'):
            os.system(
                'grep -v "^#" ' + path + 'call-snp_indel_proximity_filter/execution/output/ProximityFiltered.vcf | cut -f 1,2,7 | sort > ' + out + 'ProximityFiltered.txt')
        ### before merge vcfs ###
        # mutect
        if os.path.exists(
                path + 'call-depth_filter_mutect/execution/somatic_depth_filter.output.vcf') and not os.path.exists(
            out + 'mutect_somatic_depth_filter.output.txt'):
            os.system(
                'grep -v "^#" ' + path + 'call-depth_filter_mutect/execution/somatic_depth_filter.output.vcf | cut -f 1,2,7 | sort > ' + out + 'mutect_somatic_depth_filter.output.txt')
        # pindel
        if os.path.exists(
                path + 'call-depth_filter_pindel/execution/somatic_depth_filter.output.vcf') and not os.path.exists(
            out + 'pindel_somatic_depth_filter.output.txt'):
            os.system(
                'grep -v "^#" ' + path + 'call-depth_filter_pindel/execution/somatic_depth_filter.output.vcf | cut -f 1,2,7 | sort > ' + out + 'pindel_somatic_depth_filter.output.txt')
        # strelka_indel
        if os.path.exists(
                path + 'call-depth_filter_strelka_indel/execution/somatic_depth_filter.output.vcf') and not os.path.exists(
            out + 'strelka_indel_somatic_depth_filter.output.txt'):
            os.system(
                'grep -v "^#" ' + path + 'call-depth_filter_strelka_indel/execution/somatic_depth_filter.output.vcf | cut -f 1,2,7 | sort > ' + out + 'strelka_indel_somatic_depth_filter.output.txt')
        # strelka_snv
        if os.path.exists(
                path + 'call-depth_filter_strelka_snv/execution/somatic_depth_filter.output.vcf') and not os.path.exists(
            out + 'strelka_snv_somatic_depth_filter.output.txt'):
            os.system(
                'grep -v "^#" ' + path + 'call-depth_filter_strelka_snv/execution/somatic_depth_filter.output.vcf | cut -f 1,2,7 | sort > ' + out + 'strelka_snv_somatic_depth_filter.output.txt')
        # varscan_indel
        if os.path.exists(
                path + 'call-depth_filter_varscan_indel/execution/somatic_depth_filter.output.vcf') and not os.path.exists(
            out + 'varscan_indel_somatic_depth_filter.output.txt'):
            os.system(
                'grep -v "^#" ' + path + 'call-depth_filter_varscan_indel/execution/somatic_depth_filter.output.vcf | cut -f 1,2,7 | sort > ' + out + 'varscan_indel_somatic_depth_filter.output.txt')
        # varscan_snv
        if os.path.exists(
                path + 'call-depth_filter_varscan_snv/execution/somatic_depth_filter.output.vcf') and not os.path.exists(
            out + 'varscan_snv_somatic_depth_filter.output.txt'):
            os.system(
                'grep -v "^#" ' + path + 'call-depth_filter_varscan_snv/execution/somatic_depth_filter.output.vcf | cut -f 1,2,7 | sort > ' + out + 'varscan_snv_somatic_depth_filter.output.txt')


def save_filelist(filelist):
    filename = 'stored_vcf_filelist.json'
    with open(filename, 'w') as f:
        f.write(json.dumps(filelist))


def load_filelist(filename):
    with open(filename) as f:
        filelist = json.loads(f.read())
    return filelist


def load_filelist_id(filename):
    with open(filename) as f:
        filelist = json.loads(f.read())
    res = []
    for path in filelist:
        cromwell_workflow_id = re.search('[0-9|a-z]{8}-[0-9|a-z]{4}-[0-9|a-z]{4}-[0-9|a-z]{4}-[0-9|a-z]{12}',
                                         path).group(0)
        res.append(cromwell_workflow_id)
    return res
