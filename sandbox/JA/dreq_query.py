'''
Interrogate data request tables to get variables requested for each experiment.

Initial version uses python dicts from the airtable export.

Potentially improve later by defining classes representing tables & records in the data request.
'''

DREQ_VERSION = ''  # if a tagged version is being used, set this in calling script

def get_content_type(content):
    '''
    Internal function to distinguish the type of airtable export we are working with, based on the input dict.

    Parameters
    ----------
    content : dict
        Dict containing data request content exported from airtable.

    Returns
    -------
    str indicating type of content:
        'working'   3 bases containing the latest working version of data request content
        'version'   1 base containing the content of a tagged data request version
    '''
    content_type = ''
    match len(content):
        case 3:
            content_type = 'working'
        case 1:
            content_type = 'version'
    return content_type

def version_base_name():
    return f'Data Request {DREQ_VERSION}'

def get_requested_variables(content, use_opp='all', max_priority='Low', verbose=True):
    '''
    Return variables requested for each experiment, as a function of opportunities supported and priority level of variables.

    Parameters
    ----------
    content : dict
        Dict containing data request content exported from airtable.
    use_opp : str or list of str/int
        Identifies the opportunities being supported. Options:
            'all' : include all available opportunities
            integers : include opportunities identified by their integer IDs
            strings : include opportunities identified by their titles
    max_priority : str
        Variables up to this priority level will be returned.
        E.g., max_priority='Low' means all priority levels (High, Medium, Low) are returned.

    Returns
    -------
    Dict keyed by experiment name, giving prioritized variables for each experiment.
    Example:
    {'historical' :
        'High' : {'Amon.tas', 'day.tas', ...},
        'Medium' : ...
    }
    '''

    content_type = get_content_type(content)
    match content_type:
        case 'working':
            base_name = 'Data Request Opportunities (Public)'
        case 'version':
            base_name = version_base_name()

    tables = content[base_name]

    all_opps = tables['Opportunity']

    discard_empty_opps = True
    if discard_empty_opps:
        # somehow empty opportunities are in the v1.0alpha base
        # this will cause problems below
        # discard them
        discard_opp_id = []
        for opp_id, opp in all_opps['records'].items():
            if len(opp) == 0:
                discard_opp_id.append(opp_id)
        for opp_id in discard_opp_id:
            all_opps['records'].pop(opp_id)

    if use_opp == 'all':
        # Include all opportunities
        use_opp = [opp_id for opp_id in all_opps['records']]
    elif isinstance(use_opp, list):
        if all([isinstance(m, int) for m in use_opp]):
            # Opportunity IDs have been given as input
            use_opp = [opp_id for opp_id,opp in all_opps['records'].items() if int(opp['Opportunity ID']) in use_opp]
        elif all([isinstance(s, str) for s in use_opp]):
            # Assume Opportunity titles have been passed
            use_opp = [opp_id for opp_id,opp in all_opps['records'].items() if opp['Title of Opportunity'] in use_opp]
    use_opp = list(set(use_opp))
    if len(use_opp) == 0:
        print('No opportunities found')
        return
    if verbose:
        n = len(use_opp)
        print(f'Finding requested variables for {n} Opportunities:')
        for opp_id in use_opp:
            opp = all_opps['records'][opp_id]
            print('  ' + opp['Title of Opportunity'])

    # Loop over the opportunities
    expt_vars = {}
    priority_levels = ['High', 'Medium', 'Low']
    for opp_id in use_opp:
        opp = all_opps['records'][opp_id] # one record from the Opportunity table

        if 'Experiment Groups' not in opp:
            continue
        for expt_group_id in opp['Experiment Groups']:  # Loop over experiment groups in this opportunity
            expt_group = tables['Experiment Group']['records'][expt_group_id]
            # Get names of experiments in this experiment group
            for expt_id in expt_group['Experiments']:

                match content_type: # cluge, fix later
                    case 'working':
                        expt_table_name = 'Experiment'
                    case 'version':
                        expt_table_name = 'Experiments'

                expt = tables[expt_table_name]['records'][expt_id]
                expt_key = expt[' Experiment'].strip()  # Name of experiment, e.g "historical"
                if expt_key not in expt_vars:
                    expt_vars[expt_key] = {p : set() for p in priority_levels}

        if 'Variable Groups' not in opp:
            continue
        for var_group_id in opp['Variable Groups']:  # Loop over variable groups in this opportunity
            var_group = tables['Variable Group']['records'][var_group_id]
            priority = var_group['Priority Level']

            if isinstance(priority, list):  # for content_type == 'version'
                assert len(priority) == 1, 'Variable Group should have one specified priority level'
                prilev_id = priority[0]
                prilev = tables['Priority Level']['records'][prilev_id]
                priority = prilev['Name']
                assert priority in priority_levels, 'Unrecognized priority level: ' + priority
                del prilev

            # Get names of variables in this variable group
            for var_id in var_group['Variables']:  # Loop over variables in this variable group
                var = tables['Variables']['records'][var_id]
                var_key = var['Compound Name']  # Name of variable, e.g. "Amon.tas"
                for expt_key, expt_var in expt_vars.items():
                    # Add this variable to the experiment, at the priority level specified by the variable group
                    expt_var[priority].add(var_key)

    # Remove overlaps between priority levels
    for expt_key, expt_var in expt_vars.items():
        # remove from Medium priority group any variables already occuring in High priority group
        expt_var['Medium'] = expt_var['Medium'].difference(expt_var['High'])  
        # remove from Low priority group any variables already occuring in Medium priority group
        expt_var['Low'] = expt_var['Low'].difference(expt_var['Medium'])

    # Remove unwanted priority levels
    for expt_key, expt_var in expt_vars.items():
        if max_priority.lower() == 'high':
            expt_var.pop('Medium')
            expt_var.pop('Low')
        elif max_priority.lower() == 'medium':
            expt_var.pop('Low')

    return expt_vars

